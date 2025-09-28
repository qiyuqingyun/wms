from django import forms

from .models import Category, Item, ItemBatch, Location, Movement


class ScanForm(forms.Form):
    code = forms.CharField(
        max_length=64,
        label='识别编码',
        help_text='输入 SKU 或条码后回车查询',
        widget=forms.TextInput(attrs={'placeholder': 'SKU / 条码'}),
    )


class InboundForm(forms.Form):
    batch_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    item_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    item = forms.ModelChoiceField(queryset=Item.objects.select_related('category').order_by('name'), required=False, label='商品')
    batch_number = forms.CharField(max_length=100, label='批次号')
    production_date = forms.DateField(
        label='生产日期',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    expiry_date = forms.DateField(
        label='过期日期',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    barcode = forms.CharField(max_length=64, label='条码/批次码')
    quantity_units = forms.IntegerField(min_value=1, label='数量')
    location = forms.ModelChoiceField(queryset=Location.objects.all(), required=False, label='优先货位')

    def __init__(self, *args, lock_dates: bool = False, lock_item: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.lock_dates = lock_dates
        self.lock_item = lock_item
        if lock_dates:
            self.fields['production_date'].disabled = True
            self.fields['expiry_date'].disabled = True
        if lock_item:
            self.fields['item'].disabled = True


class OutboundForm(forms.Form):
    batch = forms.ModelChoiceField(
        queryset=ItemBatch.objects.filter(quantity_units__gt=0).select_related('item').order_by('-updated_at'),
        label='选择批次',
        help_text='仅显示当前还有库存的批次',
    )
    quantity_units = forms.IntegerField(min_value=1, label='数量')
    location = forms.ModelChoiceField(
        queryset=Location.objects.all().order_by('code'),
        required=False,
        label='货位（可选）',
    )
    note = forms.CharField(max_length=255, required=False, label='备注')

    def clean(self):
        cleaned = super().clean()
        batch = cleaned.get('batch')
        qty = cleaned.get('quantity_units')
        if batch is not None and qty is not None and qty > batch.quantity_units:
            from django.core.exceptions import ValidationError
            raise ValidationError('出库数量超过现有库存')
        return cleaned


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['code', 'name', 'capacity_volume', 'note']


class ItemPackagingForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['category', 'size_text', 'unit', 'packaging_volume', 'has_shelf_life', 'description', 'active']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'size_text': '包装规格',
            'unit': '单位',
            'packaging_volume': '单件体积（仓储单位）',
            'has_shelf_life': '是否有保质期',
            'description': '描述说明',
            'active': '是否启用',
        }
        help_texts = {
            'packaging_volume': '用于计算货位占用的体积，建议填写实际体积或换算后的仓储单位。',
        }


