from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from core.models import Paciente, UserProfile
from .models import Historial, Turno
from .forms import HistorialForm, ArchivoAdjuntoForm, TurnoForm
from core.decorators import clinico_requerido
import json

@login_required
def ficha_medica(request, paciente_id):
    """Muestra el historial completo de una mascota"""
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    historial = paciente.historial_clinico.all().order_by('-fecha')
    turnos = paciente.turnos.exclude(estado__in=['CANCELADO', 'ATENDIDO']).order_by('fecha_hora_inicio').select_related('profesional__user')
    
    return render(request, 'clinical/ficha_medica.html', {
        'paciente': paciente,
        'historial': historial,
        'turnos': turnos,
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
        form = HistorialForm(initial={'peso': paciente.peso_actual, 'fecha': timezone.now()})
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


# =============================================================================
# MÓDULO DE AGENDA / TURNERO
# =============================================================================

@login_required
def agenda(request):
    """Vista principal del calendario de turnos."""
    empresa = request.user.profile.empresa
    veterinarios = UserProfile.objects.filter(
        empresa=empresa, rol='VETERINARIO'
    ).select_related('user')
    pacientes = Paciente.objects.filter(empresa=empresa).select_related('cliente')

    # Pre-selección desde enlaces de Paciente o Cliente
    preselect_paciente = request.GET.get('paciente', '')
    preselect_cliente = request.GET.get('cliente', '')

    return render(request, 'clinical/agenda.html', {
        'veterinarios': veterinarios,
        'pacientes': pacientes,
        'preselect_paciente': preselect_paciente,
        'preselect_cliente': preselect_cliente,
    })


@login_required
@require_GET
def api_turnos(request):
    """Feed JSON para FullCalendar. Filtra por rango start/end y empresa."""
    empresa = request.user.profile.empresa
    start = request.GET.get('start')
    end = request.GET.get('end')

    turnos = Turno.objects.filter(empresa=empresa).select_related('paciente', 'profesional__user')

    if start:
        turnos = turnos.filter(fecha_hora_inicio__gte=start)
    if end:
        turnos = turnos.filter(fecha_hora_fin__lte=end)

    eventos = []
    for t in turnos:
        eventos.append({
            'id': t.id,
            'title': f"{t.paciente.nombre} - {t.motivo}",
            'start': t.fecha_hora_inicio.isoformat(),
            'end': t.fecha_hora_fin.isoformat(),
            'color': t.color,
            'extendedProps': {
                'paciente_id': t.paciente.id,
                'profesional_id': t.profesional.id,
                'profesional_nombre': t.profesional.user.get_full_name() or t.profesional.user.username,
                'motivo': t.motivo,
                'estado': t.estado,
                'notas': t.notas,
            }
        })

    return JsonResponse(eventos, safe=False)


@login_required
@require_POST
def crear_turno(request):
    """Crea un turno nuevo desde el modal del calendario."""
    empresa = request.user.profile.empresa

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'JSON inválido.'}, status=400)

    form = TurnoForm(data, empresa=empresa)
    if form.is_valid():
        turno = form.save(commit=False)
        turno.empresa = empresa
        turno.save()
        return JsonResponse({
            'ok': True,
            'turno': {
                'id': turno.id,
                'title': f"{turno.paciente.nombre} - {turno.motivo}",
                'start': turno.fecha_hora_inicio.isoformat(),
                'end': turno.fecha_hora_fin.isoformat(),
                'color': turno.color,
            }
        })
    else:
        return JsonResponse({'ok': False, 'errores': form.errors}, status=400)


@login_required
@require_POST
def editar_turno(request, turno_id):
    """Actualiza un turno (modal o drag & drop)."""
    empresa = request.user.profile.empresa
    turno = get_object_or_404(Turno, pk=turno_id, empresa=empresa)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'JSON inválido.'}, status=400)

    form = TurnoForm(data, instance=turno, empresa=empresa)
    if form.is_valid():
        form.save()
        return JsonResponse({
            'ok': True,
            'turno': {
                'id': turno.id,
                'title': f"{turno.paciente.nombre} - {turno.motivo}",
                'start': turno.fecha_hora_inicio.isoformat(),
                'end': turno.fecha_hora_fin.isoformat(),
                'color': turno.color,
            }
        })
    else:
        return JsonResponse({'ok': False, 'errores': form.errors}, status=400)


@login_required
@require_POST
def cancelar_turno(request, turno_id):
    """Cambia el estado del turno a CANCELADO."""
    empresa = request.user.profile.empresa
    turno = get_object_or_404(Turno, pk=turno_id, empresa=empresa)
    turno.estado = 'CANCELADO'
    turno.save()
    return JsonResponse({'ok': True, 'color': turno.color})


@login_required
@require_POST
def atender_turno(request, turno_id):
    """Marca el turno como ATENDIDO y opcionalmente crea una entrada de historia clínica."""
    empresa = request.user.profile.empresa
    turno = get_object_or_404(Turno, pk=turno_id, empresa=empresa)
    turno.estado = 'ATENDIDO'
    turno.save()

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = {}

    crear_historial = data.get('crear_historial', False)
    historial_id = None

    if crear_historial:
        historial = Historial.objects.create(
            paciente=turno.paciente,
            motivo=turno.motivo,
            anamnesis=turno.notas,
        )
        historial_id = historial.id

    return JsonResponse({
        'ok': True,
        'color': turno.color,
        'historial_id': historial_id,
        'paciente_id': turno.paciente.id,
    })
