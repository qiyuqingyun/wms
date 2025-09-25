from django.contrib import admin

from .models import BatchLocation, Category, Item, ItemBatch, ItemImage, Location, Movement


class ItemImageInline(admin.TabularInline):
    model = ItemImage
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku_code', 'category', 'unit', 'packaging_volume', 'active')
    list_filter = ('category', 'active', 'has_shelf_life')
    search_fields = ('name', 'sku_code')
    inlines = [ItemImageInline]


@admin.register(ItemBatch)
class ItemBatchAdmin(admin.ModelAdmin):
    list_display = ('item', 'batch_number', 'barcode', 'production_date', 'expiry_date', 'quantity_units')
    search_fields = ('batch_number', 'barcode', 'item__name', 'item__sku_code')
    list_filter = ('expiry_date', 'item__category')


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'capacity_volume')
    search_fields = ('code', 'name')


@admin.register(BatchLocation)
class BatchLocationAdmin(admin.ModelAdmin):
    list_display = ('batch', 'location', 'quantity_units')
    search_fields = ('batch__batch_number', 'batch__item__name', 'location__code')


@admin.register(Movement)
class MovementAdmin(admin.ModelAdmin):
    list_display = ('direction', 'batch', 'quantity_units', 'user', 'location', 'created_at')
    list_filter = ('direction', 'created_at')
    search_fields = ('batch__batch_number', 'batch__item__name')
