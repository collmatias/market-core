from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from .models import Cliente, Paciente, HistoriaClinica
from .serializers import ClienteSerializer, PacienteSerializer, HistoriaClinicaSerializer

from django.shortcuts import render
from .forms import ClienteForm 

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all().order_by('-id')
    serializer_class = ClienteSerializer

class PacienteViewSet(viewsets.ModelViewSet):
    queryset = Paciente.objects.all().order_by('-id')
    serializer_class = PacienteSerializer

class HistoriaClinicaViewSet(viewsets.ModelViewSet):
    queryset = HistoriaClinica.objects.all().order_by('-fecha')
    serializer_class = HistoriaClinicaSerializer


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