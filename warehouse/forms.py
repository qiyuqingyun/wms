from django import forms

from .models import Category, Item, ItemBatch, Location, Movement


class ScanForm(forms.Form):
    code = forms.CharField(
        max_length=64,
        label='数字识别码',
        help_text='输入 SKU 或批次条码后回车',
        widget=forms.TextInput(attrs={'placeholder': 'SKU / 批次条码'}),
    )


class InboundForm(forms.Form):
    batch_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    item_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    batch_number = forms.CharField(max_length=100, label='批次号')
    production_date = forms.DateField(label='生产日期', required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    expiry_date = forms.DateField(label='过期日期', required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    barcode = forms.CharField(max_length=64, label='批次条码')
    quantity_units = forms.IntegerField(min_value=1, label='数量')
    location = forms.ModelChoiceField(queryset=Location.objects.all(), required=False, label='优先货位')


class OutboundForm(forms.Form):
    batch = forms.ModelChoiceField(
        queryset=ItemBatch.objects.filter(quantity_units__gt=0).select_related('item').order_by('-updated_at'),
        label='选择批次',
        help_text='仅显示当前仍有库存的批次',
    )
    quantity_units = forms.IntegerField(min_value=1, label='数量')
    location = forms.ModelChoiceField(
        queryset=Location.objects.all().order_by('code'),
        required=False,
        label='货位（可选）',
    )
    note = forms.CharField(max_length=255, required=False, label='备注')


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
            'packaging_volume': '单件体积（立方）',
            'has_shelf_life': '是否有保质期',
            'description': '补充说明',
            'active': '是否启用',
        }
        help_texts = {
            'packaging_volume': '用于计算货位容量占用，单位立方米或按实际标准',
        }
