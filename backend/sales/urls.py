from django.urls import path
from . import views

urlpatterns = [
    path('pos/', views.new_sale, name='new_sale'),
    path('pos/report/', views.cash_report, name='cash_report'),
    path('sales/', views.sale_list, name='sale_list'),
    path('sales/<int:sale_id>/ticket/', views.sale_detail, name='sale_detail'),
]
