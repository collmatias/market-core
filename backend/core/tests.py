from django.test import TestCase, Client
from django.urls import reverse

class SecurityTest(TestCase):
    def setUp(self):
        # Cliente SIN loguearse
        self.client = Client()

    def test_acceso_denegado_sin_login(self):
        """Intenta entrar a clientes sin login y espera redirección"""
        response = self.client.get('/clientes/')
        
        # 302 es el código de redirección
        self.assertEqual(response.status_code, 302) 
        
        # Verifica que nos mande a /login/
        self.assertIn('/login/', response.url)