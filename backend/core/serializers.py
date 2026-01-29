from rest_framework import serializers
from .models import Cliente, Paciente, HistoriaClinica

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'

class PacienteSerializer(serializers.ModelSerializer):
    # Para que al leer muestre el nombre del dueño en vez del ID
    nombre_cliente = serializers.ReadOnlyField(source='cliente.nombre')
    apellido_cliente = serializers.ReadOnlyField(source='cliente.apellido')

    class Meta:
        model = Paciente
        fields = '__all__'

class HistoriaClinicaSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoriaClinica
        fields = '__all__'