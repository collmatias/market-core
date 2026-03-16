from django.contrib import admin
from .models import Historial, ArchivoAdjunto, Turno

# Esto permite ver/subir archivos directamente dentro de la pantalla del Historial
class ArchivoAdjuntoInline(admin.TabularInline):
    model = ArchivoAdjunto
    extra = 1  # Muestra 1 renglón vacío para agregar nuevo archivo

@admin.register(Historial)
class HistorialAdmin(admin.ModelAdmin):
    # Qué columnas ver en la lista
    list_display = ('fecha', 'paciente', 'motivo', 'diagnostico', 'peso')
    
    # Buscador: permite buscar por nombre de mascota o apellido del dueño
    search_fields = ('paciente__nombre', 'paciente__cliente__apellido', 'motivo')
    
    # Filtros laterales
    list_filter = ('fecha',)
    
    # Agregamos los adjuntos aquí dentro
    inlines = [ArchivoAdjuntoInline]

# Si quieres ver los archivos sueltos también, descomenta esto:
# admin.site.register(ArchivoAdjunto)

@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ('fecha_hora_inicio', 'paciente', 'profesional', 'motivo', 'estado')
    list_filter = ('estado', 'fecha_hora_inicio', 'profesional')
    search_fields = ('paciente__nombre', 'motivo')