from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='platform_dashboard'),
    path('licenses/', views.license_list, name='platform_license_list'),
    path('licenses/create/', views.license_create, name='platform_license_create'),
    path('licenses/<str:hw_id>/', views.license_detail, name='platform_license_detail'),
    path('licenses/<str:hw_id>/revoke/', views.license_revoke, name='platform_license_revoke'),
    path('licenses/<str:hw_id>/reset-password/', views.force_password_reset, name='platform_force_password_reset'),
    path('licenses/transfer/', views.license_transfer, name='platform_license_transfer'),
]
