from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MedicalRecord


@receiver(post_save, sender=MedicalRecord)
def update_patient_weight(sender, instance, created, **kwargs):
    if instance.weight:
        patient = instance.patient
        patient.current_weight = instance.weight
        patient.save()
