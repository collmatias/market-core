from django.contrib import admin
from .models import Product, StockMovement


class ProductAdmin(admin.ModelAdmin):
    list_display = ('description', 'sale_price', 'current_stock', 'needs_restock')

admin.site.register(Product, ProductAdmin)
admin.site.register(StockMovement)
