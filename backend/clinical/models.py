from django.db import models
from django.utils import timezone
from core.models import Paciente

class Historial(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='historial_clinico')
    fecha = models.DateTimeField(default=timezone.now)
    motivo = models.CharField(max_length=200, help_text="Ej: Vómitos, Vacunación, Control")
    anamnesis = models.TextField(verbose_name="Anamnesis / Observaciones", blank=True)
    diagnostico = models.TextField(verbose_name="Diagnóstico", blank=True)
    tratamiento = models.TextField(verbose_name="Tratamiento / Indicaciones", blank=True)
    peso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Peso en KG")
    
    # Próxima visita (Recordatorio simple)
    proxima_visita = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.fecha.strftime('%d/%m/%Y')} - {self.paciente.nombre}"

class ArchivoAdjunto(models.Model):
    historial = models.ForeignKey(Historial, on_delete=models.CASCADE, related_name='adjuntos')
    archivo = models.FileField(upload_to='historias_clinicas/%Y/%m/')
    descripcion = models.CharField(max_length=100, blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Archivo de {self.historial.paciente.nombre}"