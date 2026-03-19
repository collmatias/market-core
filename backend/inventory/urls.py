from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.product_list, name='product_list'),
    path('products/new/', views.create_product, name='create_product'),
    path('products/edit/<int:id>/', views.edit_product, name='edit_product'),
    path('products/delete/<int:id>/', views.delete_product, name='delete_product'),
    path('products/labels/', views.product_labels, name='product_labels'),
    path('stock/movement/', views.register_movement, name='register_movement'),
    path('catalog/lookup/', views.catalog_lookup, name='catalog_lookup'),
    path('catalog/import/', views.catalog_import, name='catalog_import'),
]
