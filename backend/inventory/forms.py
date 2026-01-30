from django import forms
from .models import Producto, MovimientoStock

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['codigo_barras', 'descripcion', 'tipo', 'costo', 'precio_venta', 'cantidad_minima']
        widgets = {
            'codigo_barras': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'costo': forms.NumberInput(attrs={'class': 'form-control'}),
            'precio_venta': forms.NumberInput(attrs={'class': 'form-control'}),
            'cantidad_minima': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class MovimientoStockForm(forms.ModelForm):
    class Meta:
        model = MovimientoStock
        fields = ['producto', 'tipo', 'cantidad']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # En el selector de movimientos, solo mostramos productos físicos (no servicios)
        self.fields['producto'].queryset = Producto.objects.filter(tipo='PRODUCTO')