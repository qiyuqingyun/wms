from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models import Count, Prefetch, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    InboundForm,
    ItemPackagingForm,
    LocationForm,
    OutboundForm,
    ScanForm,
)
from .models import BatchLocation, Category, Item, ItemBatch, Location, Movement
from .services import allocate_inbound, release_outbound


@login_required
def dashboard(request):
    items_count = Item.objects.count()
    batches_count = ItemBatch.objects.count()
    near_expiry_count = ItemBatch.objects.filter(
        expiry_date__isnull=False,
        expiry_date__lte=timezone.localdate() + timezone.timedelta(days=30),
    ).count()
    context = {
        'items_count': items_count,
        'batches_count': batches_count,
        'near_expiry_count': near_expiry_count,
    }
    return render(request, 'warehouse/dashboard.html', context)


@login_required
def catalog(request):
    item_qs = (
        Item.objects.filter(active=True)
        .select_related('category')
        .prefetch_related('images')
        .order_by('name')
    )
    categories = (
        Category.objects.order_by('order', 'name')
        .prefetch_related(Prefetch('items', queryset=item_qs))
    )
    return render(request, 'warehouse/catalog.html', {'categories': categories})


@login_required
def scan_view(request):
    form = ScanForm(request.GET or None)
    item = None
    batch = None
    batches = None
    if form.is_valid():
        code = form.cleaned_data['code']
        batch = ItemBatch.objects.filter(barcode=code).select_related('item').first()
        if batch:
            item = batch.item
        else:
            item = Item.objects.filter(sku_code=code).first()
            if item:
                batches = item.batches.order_by('-created_at')
            else:
                messages.warning(request, '未找到匹配的商品或批次')
    return render(
        request,
        'warehouse/scan.html',
        {
            'form': form,
            'item': item,
            'batch': batch,
            'batches': batches,
            'can_edit_packaging': request.user.has_perm('warehouse.change_item'),
        },
    )




@login_required
@permission_required('warehouse.add_movement', raise_exception=True)
@transaction.atomic
def inbound_view(request):
    if request.method == 'POST':
        form = InboundForm(request.POST)
        if form.is_valid():
            batch_id = form.cleaned_data.get('batch_id')
            item_id = form.cleaned_data.get('item_id')
            location = form.cleaned_data.get('location')
            if batch_id:
                batch = get_object_or_404(ItemBatch, id=batch_id)
            else:
                item = get_object_or_404(Item, id=item_id)
                batch, created = ItemBatch.objects.get_or_create(
                    item=item,
                    batch_number=form.cleaned_data['batch_number'],
                    defaults={
                        'production_date': form.cleaned_data.get('production_date'),
                        'expiry_date': form.cleaned_data.get('expiry_date'),
                        'barcode': form.cleaned_data['barcode'],
                        'quantity_units': 0,
                    },
                )
                if not created:
                    batch.production_date = form.cleaned_data.get('production_date')
                    batch.expiry_date = form.cleaned_data.get('expiry_date')
                    batch.barcode = form.cleaned_data['barcode']
                    batch.save()

            qty = form.cleaned_data['quantity_units']
            allocation = allocate_inbound(batch, qty, preferred=location)
            Movement.objects.create(
                batch=batch,
                direction=Movement.Direction.IN,
                quantity_units=qty,
                user=request.user,
                location=location,
                note='扫码入库',
            )
            unit_name = batch.item.unit or '件'
            if allocation.assignments:
                assigned_text = '，'.join(f"{loc.code}:{units}{unit_name}" for loc, units in allocation.assignments)
                messages.info(request, f'自动分配到货位：{assigned_text}')
            if allocation.remaining_units > 0:
                messages.warning(request, f'货位不足，未分配货位的数量为 {allocation.remaining_units}{unit_name}')
            messages.success(request, '入库成功')
            return redirect('warehouse:scan')
    else:
        initial: dict[str, object] = {}
        if 'batch' in request.GET:
            batch = get_object_or_404(ItemBatch, id=request.GET['batch'])
            initial.update(
                {
                    'batch_id': batch.id,
                    'item_id': batch.item.id,
                    'batch_number': batch.batch_number,
                    'production_date': batch.production_date,
                    'expiry_date': batch.expiry_date,
                    'barcode': batch.barcode,
                }
            )
        elif 'item' in request.GET:
            item = get_object_or_404(Item, id=request.GET['item'])
            initial['item_id'] = item.id
        form = InboundForm(initial=initial)
    return render(request, 'warehouse/inbound.html', {'form': form})


@login_required
@permission_required('warehouse.add_movement', raise_exception=True)
@transaction.atomic
def outbound_view(request):
    if request.method == 'POST':
        form = OutboundForm(request.POST)
        if form.is_valid():
            batch = form.cleaned_data['batch']
            qty = form.cleaned_data['quantity_units']
            location = form.cleaned_data.get('location')
            if qty > batch.quantity_units:
                messages.error(request, '出库数量超过库存')
            else:
                result = release_outbound(batch, qty, preferred=location)
                Movement.objects.create(
                    batch=batch,
                    direction=Movement.Direction.OUT,
                    quantity_units=qty,
                    user=request.user,
                    location=location,
                    note=form.cleaned_data.get('note', ''),
                )
                unit_name = batch.item.unit or '件'
                if result.assignments:
                    removed_text = '，'.join(f"{loc.code}:{units}{unit_name}" for loc, units in result.assignments)
                    messages.info(request, f'已从货位扣减：{removed_text}')
                if result.removed_units < qty:
                    diff = qty - result.removed_units
                    messages.warning(request, f'仍有 {diff}{unit_name}库存未找到对应货位，请稍后核实')
                messages.success(request, '出库成功')
                return redirect('warehouse:scan')
    else:
        initial: dict[str, object] = {}
        batch_id = request.GET.get('batch')
        if batch_id:
            try:
                initial_batch = ItemBatch.objects.get(pk=batch_id)
                initial['batch'] = initial_batch
            except ItemBatch.DoesNotExist:
                pass
        form = OutboundForm(initial=initial)
    return render(request, 'warehouse/outbound.html', {'form': form})


@login_required
def near_expiry(request):
    today = timezone.localdate()
    threshold = today + timezone.timedelta(days=30)
    batches = (
        ItemBatch.objects.filter(
            expiry_date__isnull=False,
            expiry_date__lte=threshold,
            quantity_units__gt=0,
        )
        .select_related('item')
        .order_by('expiry_date')
    )
    return render(request, 'warehouse/near_expiry.html', {'batches': batches, 'today': today})


@login_required
def popular_items(request):
    popular = (
        Movement.objects
        .values('batch__item__id', 'batch__item__name', 'batch__item__sku_code')
        .annotate(moves=Count('id'))
        .order_by('-moves')[:20]
    )
    return render(request, 'warehouse/popular.html', {'popular': popular})


@login_required
@permission_required('warehouse.view_location', raise_exception=True)
def locations(request):
    locs = Location.objects.all().order_by('code')
    return render(request, 'warehouse/locations.html', {'locations': locs})


@login_required
@permission_required('warehouse.add_location', raise_exception=True)
def location_new(request):
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '新增货位成功')
            return redirect('warehouse:locations')
    else:
        form = LocationForm()
    return render(request, 'warehouse/location_form.html', {'form': form})


@login_required
def inventory_summary(request):
    today = timezone.localdate()
    threshold = today + timezone.timedelta(days=30)
    base_rows = (
        ItemBatch.objects.select_related('item', 'item__category')
        .values(
            'item_id',
            'item__name',
            'item__sku_code',
            'item__unit',
            'item__size_text',
            'item__category__name',
        )
        .annotate(
            total_units=Sum('quantity_units'),
            near_expiry_units=Sum(
                'quantity_units',
                filter=Q(expiry_date__isnull=False, expiry_date__lte=threshold),
            ),
            batch_count=Count('id'),
        )
        .order_by('item__name')
    )
    location_rows = (
        BatchLocation.objects.select_related('batch__item', 'location')
        .values('batch__item_id', 'location__code', 'location__name')
        .annotate(units=Sum('quantity_units'))
    )
    location_map: dict[int, list[dict[str, object]]] = {}
    for row in location_rows:
        location_map.setdefault(row['batch__item_id'], []).append(row)

    inventory_rows: list[dict[str, object]] = []
    for row in base_rows:
        item_row = dict(row)
        item_row['near_expiry_units'] = item_row['near_expiry_units'] or 0
        item_row['locations'] = location_map.get(row['item_id'], [])
        inventory_rows.append(item_row)

    near_expiry_batches = (
        ItemBatch.objects.filter(
            expiry_date__isnull=False,
            expiry_date__lte=threshold,
            quantity_units__gt=0,
        )
        .select_related('item', 'item__category')
        .order_by('expiry_date')
    )
    return render(
        request,
        'warehouse/inventory.html',
        {
            'inventory_rows': inventory_rows,
            'near_expiry_batches': near_expiry_batches,
            'threshold': threshold,
        },
    )


@login_required
@permission_required('warehouse.view_item', raise_exception=True)
def item_packaging_list(request):
    qs = Item.objects.select_related('category').order_by('name')
    keyword = request.GET.get('q')
    category_slug = request.GET.get('category')
    if keyword:
        qs = qs.filter(Q(name__icontains=keyword) | Q(sku_code__icontains=keyword))
    if category_slug:
        qs = qs.filter(category__slug=category_slug)
    categories = Category.objects.order_by('order', 'name')
    return render(
        request,
        'warehouse/packaging_list.html',
        {
            'items': qs,
            'categories': categories,
            'keyword': keyword or '',
            'active_category': category_slug or '',
        },
    )


@login_required
@permission_required('warehouse.change_item', raise_exception=True)
def item_packaging_update(request, pk: int):
    item = get_object_or_404(Item.objects.select_related('category'), pk=pk)
    if request.method == 'POST':
        form = ItemPackagingForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, '包装信息已更新')
            return redirect('warehouse:packaging_list')
    else:
        form = ItemPackagingForm(instance=item)
    return render(request, 'warehouse/packaging_form.html', {'form': form, 'item': item})
