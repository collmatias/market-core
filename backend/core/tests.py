from datetime import date, timedelta

from django.test import TestCase, Client
from django.contrib.auth.models import User

from core.models import Company


class SecurityTest(TestCase):
    def setUp(self):
        self.client = Client()
        Company.objects.create(
            name='Test Store', tax_id='00-00000000-0',
            plan='TRIAL', expiration_date=date.today() + timedelta(days=30),
            is_active=True,
        )
        User.objects.create_user(username='existing', password='pass1234')

    def test_access_denied_without_login(self):
        """Tries to access clients without login and expects a redirect"""
        response = self.client.get('/clients/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)