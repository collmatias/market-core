from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Producto, MovimientoStock

class ProductoAdmin(admin.ModelAdmin):
    list_display = ('descripcion', 'precio_venta', 'cantidad_actual', 'necesita_reposicion')

admin.site.register(Producto, ProductoAdmin)
admin.site.register(MovimientoStock)