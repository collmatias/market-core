from django.contrib import admin
from .models import Venta, DetalleVenta

class DetalleInline(admin.TabularInline):
    model = DetalleVenta
    extra = 1
    # Campos de solo lectura para evitar trampas posteriores
    readonly_fields = ('subtotal',)

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    inlines = [DetalleInline]
    list_display = ('id', 'fecha', 'cliente', 'total', 'metodo_pago')
    list_filter = ('fecha', 'metodo_pago')
    search_fields = ('cliente__apellido',)