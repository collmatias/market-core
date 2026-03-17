from django.contrib import admin
from .models import MedicalRecord, Attachment, Appointment


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 1


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('date', 'patient', 'reason', 'diagnosis', 'weight')
    search_fields = ('patient__name', 'patient__owner__last_name', 'reason')
    list_filter = ('date',)
    inlines = [AttachmentInline]


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'patient', 'professional', 'reason', 'status')
    list_filter = ('status', 'start_time', 'professional')
    search_fields = ('patient__name', 'reason')
