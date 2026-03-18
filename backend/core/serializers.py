from rest_framework import serializers
from .models import Client, Patient


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'


class PatientSerializer(serializers.ModelSerializer):
    owner_first_name = serializers.ReadOnlyField(source='owner.first_name')
    owner_last_name = serializers.ReadOnlyField(source='owner.last_name')

    class Meta:
        model = Patient
        fields = '__all__'
