from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    # --- HOME & AUTH ---
    path('', views.home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # --- PROFILE ---
    path('profile/change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('profile/change-pin/', views.change_pin, name='change_pin'),

    # --- QUICK USER SWITCH ---
    path('switch-user/prepare/', views.prepare_quick_switch, name='prepare_quick_switch'),
    path('switch-user/login/', views.lockscreen, name='lockscreen'),

    # --- SYSTEM ---
    path('setup/', views.setup_wizard, name='setup_wizard'),
    path('activate/', views.activation, name='activation'),
    path('settings/', views.company_settings, name='company_settings'),
    path('settings/backup/', views.download_backup, name='download_backup'),
    path('settings/backup/restore/', views.restore_backup, name='restore_backup'),

    # --- CLIENTS ---
    path('clients/', views.client_list, name='client_list'),
    path('clients/new/', views.create_client, name='create_client'),
    path('clients/<int:client_id>/', views.client_detail, name='client_detail'),
    path('clients/<int:client_id>/edit/', views.edit_client, name='edit_client'),

    # --- TEAM ---
    path('team/', views.team_management, name='team_management'),
    path('team/edit/<int:id>/', views.edit_employee, name='edit_employee'),
    path('team/status/<int:id>/', views.toggle_employee_status, name='toggle_employee_status'),
    path('team/password/<int:id>/', views.reset_employee_password, name='reset_employee_password'),
]
