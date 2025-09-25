from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone


User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='名称')
    slug = models.SlugField(max_length=120, unique=True, verbose_name='别名', help_text='用于URL或筛选的唯一标识')
    description = models.TextField(blank=True, verbose_name='描述')
    order = models.PositiveIntegerField(default=0, verbose_name='排序', help_text='数字越小越靠前')

    class Meta:
        ordering = ('order', 'name')
        verbose_name = '物品分类'
        verbose_name_plural = '物品分类'

    def __str__(self) -> str:
        return self.name


class Item(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='items', verbose_name='分类')
    name = models.CharField(max_length=200, verbose_name='名称')
    sku_code = models.CharField(max_length=64, unique=True, verbose_name='SKU 编码', help_text='数字识别码（扫码或输入）')
    size_text = models.CharField(max_length=120, blank=True, verbose_name='尺寸/包装', help_text='包装规格或尺寸描述')
    unit = models.CharField(max_length=20, default='件', verbose_name='计量单位')
    packaging_volume = models.DecimalField(max_digits=10, decimal_places=3, default=1.0, verbose_name='单件体积', help_text='用于计算货位容量占用')
    has_shelf_life = models.BooleanField(default=False, verbose_name='是否有保质期')
    description = models.TextField(blank=True, verbose_name='描述')
    active = models.BooleanField(default=True, verbose_name='启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        ordering = ('name',)
        verbose_name = '商品'
        verbose_name_plural = '商品'

    def __str__(self) -> str:
        return f"{self.name}({self.sku_code})"


class ItemImage(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='images', verbose_name='商品')
    image = models.ImageField(upload_to='item_images/', verbose_name='图片')
    alt = models.CharField(max_length=200, blank=True, verbose_name='替代文本')

    class Meta:
        verbose_name = '商品图片'
        verbose_name_plural = '商品图片'

    def __str__(self) -> str:
        return f"{self.item.name} 图片"


class Location(models.Model):
    code = models.CharField(max_length=64, unique=True, verbose_name='编码')
    name = models.CharField(max_length=120, verbose_name='名称')
    capacity_volume = models.DecimalField(max_digits=12, decimal_places=3, verbose_name='容积')
    note = models.CharField(max_length=255, blank=True, verbose_name='备注')

    class Meta:
        ordering = ('code',)
        verbose_name = '仓储位置'
        verbose_name_plural = '仓储位置'

    def __str__(self) -> str:
        return f"{self.code}-{self.name}"

    @property
    def used_volume(self) -> float:
        total = 0.0
        for bl in self.batch_locations.select_related('batch__item').all():
            total += float(bl.quantity_units) * float(bl.batch.item.packaging_volume)
        return total

    @property
    def available_volume(self) -> float:
        return float(self.capacity_volume) - self.used_volume


class ItemBatch(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='batches', verbose_name='商品')
    batch_number = models.CharField(max_length=100, verbose_name='批次号')
    production_date = models.DateField(null=True, blank=True, verbose_name='生产日期')
    expiry_date = models.DateField(null=True, blank=True, verbose_name='过期日期')
    barcode = models.CharField(max_length=64, unique=True, verbose_name='批次条码', help_text='批次识别码（数字）')
    quantity_units = models.PositiveIntegerField(default=0, verbose_name='库存数量')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        unique_together = ('item', 'batch_number')
        ordering = ('item__name', 'batch_number')
        verbose_name = '商品批次'
        verbose_name_plural = '商品批次'

    def __str__(self) -> str:
        return f"{self.item.name} 批次:{self.batch_number} 数量:{self.quantity_units}"

    @property
    def is_near_expiry(self) -> bool:
        if not self.expiry_date:
            return False
        return 0 <= (self.expiry_date - timezone.localdate()).days <= 30


class BatchLocation(models.Model):
    batch = models.ForeignKey(ItemBatch, on_delete=models.CASCADE, related_name='locations', verbose_name='批次')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='batch_locations', verbose_name='货位')
    quantity_units = models.PositiveIntegerField(default=0, verbose_name='数量')

    class Meta:
        unique_together = ('batch', 'location')
        verbose_name = '批次货位'
        verbose_name_plural = '批次货位'

    def __str__(self) -> str:
        return f"{self.batch} @ {self.location} x{self.quantity_units}"


class Movement(models.Model):
    class Direction(models.TextChoices):
        IN = 'IN', '入库'
        OUT = 'OUT', '出库'

    batch = models.ForeignKey(ItemBatch, on_delete=models.CASCADE, related_name='movements', verbose_name='批次')
    direction = models.CharField(max_length=3, choices=Direction.choices, verbose_name='方向')
    quantity_units = models.PositiveIntegerField(verbose_name='数量')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='操作人')
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='货位')
    note = models.CharField(max_length=255, blank=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        ordering = ('-created_at',)
        verbose_name = '出入库明细'
        verbose_name_plural = '出入库明细'

    def __str__(self) -> str:
        return f"{self.get_direction_display()} {self.batch} x{self.quantity_units}"
