from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

# Create your views here.
from rest_framework import viewsets
from .models import Cliente, Paciente, HistoriaClinica
from .serializers import ClienteSerializer, PacienteSerializer, HistoriaClinicaSerializer

from django.shortcuts import render
from .utils import get_server_ip
from .forms import ClienteForm, PacienteForm

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all().order_by('-id')
    serializer_class = ClienteSerializer

class PacienteViewSet(viewsets.ModelViewSet):
    queryset = Paciente.objects.all().order_by('-id')
    serializer_class = PacienteSerializer

class HistoriaClinicaViewSet(viewsets.ModelViewSet):
    queryset = HistoriaClinica.objects.all().order_by('-fecha')
    serializer_class = HistoriaClinicaSerializer

def home(request):
    ip_address = get_server_ip()
    return render(request, 'core/home.html', {'server_ip': ip_address})

# --- VISTAS PARA TEMPLATES (Frontend) ---

def lista_clientes(request):
    clientes = Cliente.objects.all().order_by('-id')
    return render(request, 'core/lista_clientes.html', {'clientes': clientes})

def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_clientes') # Vuelve a la lista tras guardar
    else:
        form = ClienteForm()
    
    return render(request, 'core/cliente_form.html', {'form': form})

# --- VISTAS DE PACIENTES ---

def lista_pacientes(request):
    # select_related optimiza la consulta SQL para traer al dueño en el mismo query
    pacientes = Paciente.objects.select_related('cliente').all().order_by('-id')
    return render(request, 'core/lista_pacientes.html', {'pacientes': pacientes})

def crear_paciente(request):
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_pacientes')
    else:
        form = PacienteForm()
    
    return render(request, 'core/paciente_form.html', {'form': form})