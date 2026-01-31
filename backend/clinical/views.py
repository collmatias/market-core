from django.shortcuts import render, redirect, get_object_or_404
from core.models import Paciente
from .models import Historial
from .forms import HistorialForm, ArchivoAdjuntoForm

def ficha_medica(request, paciente_id):
    """Muestra el historial completo de una mascota"""
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    historial = paciente.historial_clinico.all().order_by('-fecha')
    
    return render(request, 'clinical/ficha_medica.html', {
        'paciente': paciente,
        'historial': historial
    })

def nueva_consulta(request, paciente_id):
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    
    if request.method == 'POST':
        form = HistorialForm(request.POST)
        archivo_form = ArchivoAdjuntoForm(request.POST, request.FILES)
        
        if form.is_valid():
            consulta = form.save(commit=False)
            consulta.paciente = paciente
            consulta.save()
            
            # Si subió un archivo, lo guardamos
            if archivo_form.is_valid() and request.FILES.get('archivo'):
                adjunto = archivo_form.save(commit=False)
                adjunto.historial = consulta
                adjunto.save()
                
            return redirect('ficha_medica', paciente_id=paciente.id)
    else:
        form = HistorialForm()
        archivo_form = ArchivoAdjuntoForm()
    
    return render(request, 'clinical/nueva_consulta.html', {
        'form': form,
        'archivo_form': archivo_form,
        'paciente': paciente
    })


def editar_consulta(request, consulta_id):
    consulta = get_object_or_404(Historial, pk=consulta_id)
    paciente = consulta.paciente # Recuperamos el paciente desde la consulta
    
    if request.method == 'POST':
        # Pasamos 'instance=consulta' para decirle que actualice, no que cree uno nuevo
        form = HistorialForm(request.POST, instance=consulta)
        archivo_form = ArchivoAdjuntoForm(request.POST, request.FILES)
        
        if form.is_valid():
            form.save()
            
            # Si quiere agregar MÁS archivos al editar, lo permitimos
            if archivo_form.is_valid() and request.FILES.get('archivo'):
                adjunto = archivo_form.save(commit=False)
                adjunto.historial = consulta
                adjunto.save()
                
            return redirect('ficha_medica', paciente_id=paciente.id)
    else:
        # Cargamos el form con los datos existentes
        form = HistorialForm(instance=consulta)
        archivo_form = ArchivoAdjuntoForm()
    
    return render(request, 'clinical/nueva_consulta.html', {
        'form': form,
        'archivo_form': archivo_form,
        'paciente': paciente,
        'es_edicion': True # Bandera para cambiar el título en el template
    })