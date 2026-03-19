from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    # --- PUBLIC ---
    path('download/', views.landing, name='landing'),
    path('register/', views.register, name='register'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),

    # --- PASSWORD RECOVERY (SaaS) ---
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset.html',
        email_template_name='registration/password_reset_email.txt',
        subject_template_name='registration/password_reset_subject.txt',
        success_url='/password-reset/done/',
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html',
    ), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        success_url='/password-reset-complete/',
    ), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html',
    ), name='password_reset_complete'),

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
    path('settings/import/', views.import_hub, name='import_hub'),
    path('settings/import/vetter/', views.vetter_import, name='vetter_import'),
    path('settings/import/vetter/browse/', views.browse_server_dirs, name='browse_server_dirs'),
    path('settings/import/vetter/analyze/', views.vetter_analyze, name='vetter_analyze'),

    # --- CLIENTS ---
    path('clients/', views.client_list, name='client_list'),
    path('clients/new/', views.create_client, name='create_client'),
    path('clients/<int:client_id>/', views.client_detail, name='client_detail'),
    path('clients/<int:client_id>/edit/', views.edit_client, name='edit_client'),

    # --- PATIENTS ---
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/new/', views.create_patient, name='create_patient'),
    path('patients/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    path('patients/<int:patient_id>/edit/', views.edit_patient, name='edit_patient'),

    # --- TEAM ---
    path('team/', views.team_management, name='team_management'),
    path('team/edit/<int:id>/', views.edit_employee, name='edit_employee'),
    path('team/status/<int:id>/', views.toggle_employee_status, name='toggle_employee_status'),
    path('team/password/<int:id>/', views.reset_employee_password, name='reset_employee_password'),
]
