from django.db import models
from django.contrib.auth.models import User

class TenantManager(models.Manager):
    def para_empresa(self, user):
        # Filtra automáticamente por la empresa del usuario
        return self.get_queryset().filter(empresa=user.profile.empresa)

class Empresa(models.Model):
    nombre = models.CharField(max_length=100)
    cuit = models.CharField(max_length=20, unique=True)
    
    # --- AGREGAR ESTOS DOS CAMPOS ---
    direccion = models.CharField(max_length=200, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    # --------------------------------
    
    # DATOS DE LICENCIA SAAS
    plan = models.CharField(max_length=20, default='FREE')
    fecha_vencimiento = models.DateField()
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class UserProfile(models.Model):
    # ROLES DISPONIBLES
    ROLES = [
        ('ADMIN', 'Administrador / Dueño'),
        ('VETERINARIO', 'Veterinario'),
        ('VENDEDOR', 'Vendedor / Recepción'),
    ]

    # Usamos related_name='profile' para poder hacer request.user.profile
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    
    # NUEVOS CAMPOS PARA EL EQUIPO
    rol = models.CharField(max_length=20, choices=ROLES, default='VETERINARIO')
    matricula = models.CharField(max_length=50, blank=True, null=True, help_text="Obligatorio para veterinarios")
    telefono = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_rol_display()}"

    # Helper para saber si puede editar medicina (lo usaremos más adelante para permisos)
    @property
    def es_clinico(self):
        return self.rol in ['ADMIN', 'VETERINARIO']

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

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='mascotas')
    nombre = models.CharField(max_length=50)
    especie = models.CharField(max_length=10, choices=ESPECIES)
    raza = models.CharField(max_length=50, blank=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    peso_actual = models.DecimalField(max_digits=5, decimal_places=2, help_text="En Kg", null=True)
    objects = TenantManager()

    def __str__(self):
        return f"{self.nombre} ({self.get_especie_display()})"
