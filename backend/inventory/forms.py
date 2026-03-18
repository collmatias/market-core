from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Product, StockMovement


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['barcode', 'description', 'type', 'cost', 'sale_price', 'minimum_stock']
        labels = {
            'barcode': _('Barcode'),
            'description': _('Description'),
            'type': _('Type'),
            'cost': _('Cost'),
            'sale_price': _('Sale Price'),
            'minimum_stock': _('Minimum Stock'),
        }
        widgets = {
            'barcode': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'sale_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'minimum_stock': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class StockMovementForm(forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = ['product', 'type', 'quantity']
        labels = {
            'product': _('Product'),
            'type': _('Movement Type'),
            'quantity': _('Quantity'),
        }
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Product.objects.filter(type='PRODUCT')
        if company:
            qs = qs.filter(company=company)
        self.fields['product'].queryset = qs
