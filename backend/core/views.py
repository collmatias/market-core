from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from .models import Cliente, Paciente, HistoriaClinica
from .serializers import ClienteSerializer, PacienteSerializer, HistoriaClinicaSerializer

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all().order_by('-id')
    serializer_class = ClienteSerializer

class PacienteViewSet(viewsets.ModelViewSet):
    queryset = Paciente.objects.all().order_by('-id')
    serializer_class = PacienteSerializer

class HistoriaClinicaViewSet(viewsets.ModelViewSet):
    queryset = HistoriaClinica.objects.all().order_by('-fecha')
    serializer_class = HistoriaClinicaSerializer