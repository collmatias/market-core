from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Historial

@receiver(post_save, sender=Historial)
def actualizar_peso_paciente(sender, instance, created, **kwargs):
    """
    Se ejecuta automáticamente CADA VEZ que guardas una ficha médica.
    Si pusiste un peso, actualiza la ficha general de la mascota.
    """
    if instance.peso:
        # Buscamos al paciente dueño de esta historia
        paciente = instance.paciente
        
        # Le actualizamos su peso actual
        paciente.peso_actual = instance.peso
        
        # Guardamos el cambio en la tabla de Pacientes
        paciente.save()
        
        print(f"--- Peso actualizado a {instance.peso}kg para {paciente.nombre} ---")