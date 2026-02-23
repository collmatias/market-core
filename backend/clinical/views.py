from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required # <--- EL CANDADO
from core.models import Paciente
from .models import Historial
from .forms import HistorialForm, ArchivoAdjuntoForm
from core.decorators import clinico_requerido

@login_required
def ficha_medica(request, paciente_id):
    """Muestra el historial completo de una mascota"""
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    historial = paciente.historial_clinico.all().order_by('-fecha')
    
    return render(request, 'clinical/ficha_medica.html', {
        'paciente': paciente,
        'historial': historial
    })

@login_required
@clinico_requerido
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
        # --- AQUÍ RECUPERÉ LO QUE SE HABÍA PERDIDO ---
        # Pre-cargamos el peso actual del paciente
        form = HistorialForm(initial={'peso': paciente.peso_actual})
        archivo_form = ArchivoAdjuntoForm()
    
    return render(request, 'clinical/nueva_consulta.html', {
        'form': form,
        'archivo_form': archivo_form,
        'paciente': paciente
    })

@login_required
@clinico_requerido
def editar_consulta(request, consulta_id):
    consulta = get_object_or_404(Historial, pk=consulta_id)
    paciente = consulta.paciente
    
    if request.method == 'POST':
        form = HistorialForm(request.POST, instance=consulta)
        archivo_form = ArchivoAdjuntoForm(request.POST, request.FILES)
        
        if form.is_valid():
            form.save()
            
            # Si agrega archivo al editar
            if archivo_form.is_valid() and request.FILES.get('archivo'):
                adjunto = archivo_form.save(commit=False)
                adjunto.historial = consulta
                adjunto.save()
                
            return redirect('ficha_medica', paciente_id=paciente.id)
    else:
        form = HistorialForm(instance=consulta)
        archivo_form = ArchivoAdjuntoForm()
    
    return render(request, 'clinical/nueva_consulta.html', {
        'form': form,
        'archivo_form': archivo_form,
        'paciente': paciente,
        'es_edicion': True
    })
