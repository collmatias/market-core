from django.db import models
from django.utils import timezone
from core.models import Patient, Company, UserProfile, TenantManager


class MedicalRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_history')
    date = models.DateTimeField(default=timezone.now)
    reason = models.CharField(max_length=200)
    anamnesis = models.TextField(blank=True)
    diagnosis = models.TextField(blank=True)
    treatment = models.TextField(blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    next_visit = models.DateField(null=True, blank=True)
    vet_name = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.date.strftime('%d/%m/%Y')} - {self.patient.name}"


class Attachment(models.Model):
    record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='medical_records/%Y/%m/')
    description = models.CharField(max_length=100, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.record.patient.name}"


class Appointment(models.Model):
    STATUSES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ]

    STATUS_COLORS = {
        'PENDING': '#6c757d',
        'CONFIRMED': '#198754',
        'CANCELLED': '#dc3545',
        'COMPLETED': '#0d6efd',
    }

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    professional = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='appointments')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    reason = models.CharField(max_length=200)
    status = models.CharField(max_length=15, choices=STATUSES, default='PENDING')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantManager()

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return f"{self.start_time.strftime('%d/%m/%Y %H:%M')} - {self.patient.name}"

    @property
    def color(self):
        return self.STATUS_COLORS.get(self.status, '#6c757d')
