from django.test import TestCase, Client
from django.contrib.auth.models import User
from core.models import Cliente, Paciente
from clinical.models import Historial

class ClinicalSignalTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='vet', password='123')
        self.client = Client()
        self.client.login(username='vet', password='123')

        self.cliente = Cliente.objects.create(nombre="Ana", apellido="Gomez", telefono="222")
        self.paciente = Paciente.objects.create(
            cliente=self.cliente,
            nombre="Firulais",
            especie="PERRO",
            peso_actual=10.0 # Peso inicial
        )

    def test_actualizacion_automatica_peso(self):
        """Prueba que al guardar historial, se actualiza la ficha del paciente"""
        
        # Enviamos el formulario de nueva consulta con peso NUEVO (15kg)
        self.client.post(f'/pacientes/{self.paciente.id}/nueva-consulta/', {
            'motivo': 'Control',
            'peso': 15.0, # El peso cambió
            'anamnesis': 'Todo ok',
            'diagnostico': 'Sano',
            'tratamiento': 'Nada',
            'fecha': '2026-01-31 10:00'
        })

        # Recargamos al paciente desde la base de datos
        self.paciente.refresh_from_db()

        # Verificamos que el peso cambió de 10 a 15 automáticamente
        self.assertEqual(float(self.paciente.peso_actual), 15.0)