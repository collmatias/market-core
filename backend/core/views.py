import os
from django.conf import settings
from django.http import FileResponse, HttpResponse, HttpResponseNotFound
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework import viewsets

from .models import Cliente, Paciente
from .serializers import ClienteSerializer, PacienteSerializer
from .forms import ClienteForm, PacienteForm
from .utils import get_server_ip

# --- CORRECCIÓN AQUÍ: Importamos 'generate_offline_key' ---
from .license import check_license, save_license, generate_offline_key

# --- API VIEWSETS (DRF) ---
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all().order_by('-id')
    serializer_class = ClienteSerializer

class PacienteViewSet(viewsets.ModelViewSet):
    queryset = Paciente.objects.all().order_by('-id')
    serializer_class = PacienteSerializer

# --- VISTAS TEMPLATES (FRONTEND) ---

@login_required
def home(request):
    ip_address = get_server_ip()
    return render(request, 'core/home.html', {'server_ip': ip_address})

@login_required
def descargar_backup(request):
    engine = settings.DATABASES['default']['ENGINE']
    if 'sqlite3' not in engine:
        return HttpResponse(
            "El backup directo solo está disponible en Modo Cliente Local (SQLite).", 
            status=501
        )

    db_path = settings.DATABASES['default']['NAME']
    
    if os.path.exists(db_path):
        fecha = timezone.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"backup_vetcore_{fecha}.sqlite3"
        return FileResponse(open(db_path, 'rb'), as_attachment=True, filename=filename)
    else:
        return HttpResponseNotFound("El archivo de base de datos no se encuentra.")

# --- CLIENTES ---
@login_required
def lista_clientes(request):
    clientes = Cliente.objects.all().order_by('-id')
    return render(request, 'core/lista_clientes.html', {'clientes': clientes})

@login_required
def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_clientes')
    else:
        form = ClienteForm()
    return render(request, 'core/cliente_form.html', {'form': form})

@login_required
def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('lista_clientes')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'core/cliente_form.html', {'form': form, 'es_edicion': True})

# --- PACIENTES ---
@login_required
def lista_pacientes(request):
    pacientes = Paciente.objects.select_related('cliente').all().order_by('-id')
    return render(request, 'core/lista_pacientes.html', {'pacientes': pacientes})

@login_required
def crear_paciente(request):
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_pacientes')
    else:
        form = PacienteForm()
    return render(request, 'core/paciente_form.html', {'form': form})

@login_required
def editar_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    if request.method == 'POST':
        form = PacienteForm(request.POST, request.FILES, instance=paciente)
        if form.is_valid():
            form.save()
            return redirect('lista_pacientes')
    else:
        form = PacienteForm(instance=paciente)
    return render(request, 'core/paciente_form.html', {'form': form, 'es_edicion': True})

# --- SISTEMA DE ACTIVACIÓN Y LICENCIAS ---

def activacion(request):
    # 1. Verificamos si ya tiene licencia válida (Online u Offline)
    is_valid, hw_id = check_license()
    
    if is_valid:
        return redirect('home')
        
    error = None
    if request.method == 'POST':
        key_ingresada = request.POST.get('serial_key', '').strip().upper()
        
        # CASO A: Clave Online (Empieza con SUB-)
        # No validamos matemáticamente, solo guardamos y dejamos que el middleware chequee contra la API
        if key_ingresada.startswith("SUB-"):
            save_license(key_ingresada)
            return redirect('home') # El middleware hará la validación real contra tu Docker Cloud API

        # CASO B: Clave Perpetua (Offline)
        # 1. Quitamos guiones para comparar la matemática pura
        key_limpia = key_ingresada.replace('-', '') 

        # 2. Generamos la clave esperada OFFLINE
        key_esperada = generate_offline_key(hw_id)
        
        # 3. Comparamos
        if key_limpia == key_esperada:
            save_license(key_esperada) # Guardamos la limpia
            return redirect('home')
        else:
            error = "Clave incorrecta. Verifique el código o su conexión a internet."
    
    return render(request, 'core/activacion.html', {
        'hardware_id': hw_id,
        'error': error
    })