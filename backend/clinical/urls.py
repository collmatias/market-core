from django.urls import path
from . import views

urlpatterns = [
    # --- MEDICAL RECORD ---
    path('patients/<int:patient_id>/history/', views.medical_record, name='medical_record'),
    path('patients/<int:patient_id>/new-consultation/', views.new_consultation, name='new_consultation'),
    path('history/<int:consultation_id>/edit/', views.edit_consultation, name='edit_consultation'),

    # --- SCHEDULE / APPOINTMENTS ---
    path('schedule/', views.schedule, name='schedule'),
    path('api/appointments/', views.api_appointments, name='api_appointments'),
    path('api/appointments/create/', views.create_appointment, name='create_appointment'),
    path('api/appointments/<int:appointment_id>/edit/', views.edit_appointment, name='edit_appointment'),
    path('api/appointments/<int:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('api/appointments/<int:appointment_id>/complete/', views.complete_appointment, name='complete_appointment'),
]
