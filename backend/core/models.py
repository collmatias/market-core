from django.db import models

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True)
    fecha_alta = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"

class Paciente(models.Model):
    ESPECIES = [('PERRO', 'Perro'), ('GATO', 'Gato'), ('OTRO', 'Otro')]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='mascotas')
    nombre = models.CharField(max_length=50)
    especie = models.CharField(max_length=10, choices=ESPECIES)
    raza = models.CharField(max_length=50, blank=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    peso_actual = models.DecimalField(max_digits=5, decimal_places=2, help_text="En Kg", null=True)
    
    def __str__(self):
        return f"{self.nombre} ({self.get_especie_display()})"

# class HistoriaClinica(models.Model):
#     paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='historia')
#     fecha = models.DateTimeField(auto_now_add=True)
#     motivo_consulta = models.CharField(max_length=200)
#     diagnostico = models.TextField()
#     tratamiento = models.TextField()
#     observaciones = models.TextField(blank=True)
    
#     def __str__(self):
#         return f"{self.fecha.strftime('%d/%m/%Y')} - {self.paciente.nombre}"