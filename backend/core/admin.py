from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Cliente, Paciente #, HistoriaClinica

admin.site.register(Cliente)
admin.site.register(Paciente)
# admin.site.register(HistoriaClinica)