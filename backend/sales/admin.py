from django.contrib import admin
from .models import Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1
    readonly_fields = ('subtotal',)


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    inlines = [SaleItemInline]
    list_display = ('id', 'date', 'client', 'total', 'payment_method')
    list_filter = ('date', 'payment_method')
    search_fields = ('client__last_name',)
