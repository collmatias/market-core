"""
Management command: seed_demo
Wipes the database and loads realistic demo data for testing.
Usage: python manage.py seed_demo
"""
import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone

from core.models import Company, UserProfile, Client, Patient
from clinical.models import MedicalRecord, Appointment
from inventory.models import Product, StockMovement
from sales.models import Sale, SaleItem


class Command(BaseCommand):
    help = 'Wipes the DB and loads realistic demo data for a veterinary clinic'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-flush',
            action='store_true',
            help='Do not delete existing data (append on top)',
        )

    def handle(self, *args, **options):
        if not options['no_flush']:
            self.stdout.write('🗑️  Flushing database...')
            self._flush()

        self.stdout.write('🏢 Creating company...')
        company = self._create_company()

        self.stdout.write('👤 Creating users...')
        admin_user, vet1, vet2, admin_profile, vet1_profile, vet2_profile = self._create_users(company)

        self.stdout.write('🧑 Creating clients and patients...')
        clients, patients = self._create_clients_patients(company)

        self.stdout.write('📋 Creating medical records...')
        self._create_medical_records(patients)

        self.stdout.write('📅 Creating appointments...')
        self._create_appointments(company, patients, [vet1_profile, vet2_profile])

        self.stdout.write('📦 Creating products and services...')
        products = self._create_products(company)

        self.stdout.write('💰 Creating sales...')
        self._create_sales(company, clients, products, admin_user)

        self.stdout.write(self.style.SUCCESS('\n✅ Demo data loaded successfully!'))
        self.stdout.write(self.style.SUCCESS('─' * 50))
        self.stdout.write(f'   🏢 Company: {company.name}')
        self.stdout.write(f'   👤 Admin: admin / admin1234')
        self.stdout.write(f'   🩺 Vet 1: drlopez / vet1234')
        self.stdout.write(f'   🩺 Vet 2: dragomez / vet1234')
        self.stdout.write(f'   🧑 Clients: {len(clients)}')
        self.stdout.write(f'   🐾 Patients: {len(patients)}')
        self.stdout.write(f'   📦 Products: {len(products)}')
        self.stdout.write(self.style.SUCCESS('─' * 50))

    def _flush(self):
        """Delete all data in safe order (respecting FK constraints)."""
        SaleItem.objects.all().delete()
        Sale.objects.all().delete()
        StockMovement.objects.all().delete()
        Product.objects.all().delete()
        Appointment.objects.all().delete()
        MedicalRecord.objects.all().delete()
        Patient.objects.all().delete()
        Client.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.all().delete()
        Company.objects.all().delete()

    def _create_company(self):
        return Company.objects.create(
            name='Veterinaria Huellas',
            tax_id='30-71234567-9',
            address='Av. Colón 1234, Córdoba',
            phone='351-4567890',
            plan='TRIAL',
            expiration_date=date.today() + timedelta(days=90),
            is_active=True,
        )

    def _create_users(self, company):
        # Admin
        admin_user = User.objects.create_superuser(
            username='admin', email='admin@vetcore.local', password='admin1234',
            first_name='Matías', last_name='Administrador'
        )
        admin_profile = UserProfile.objects.create(
            user=admin_user, company=company, role='ADMIN',
            is_admin=True, pin='0000', avatar='bi-person-fill'
        )

        # Vet 1
        vet1 = User.objects.create_user(
            username='drlopez', email='lopez@vetcore.local', password='vet1234',
            first_name='Carlos', last_name='López'
        )
        vet1_profile = UserProfile.objects.create(
            user=vet1, company=company, role='VET',
            is_admin=False, license_number='MP-4521', pin='1111',
            avatar='bi-heart-pulse-fill'
        )

        # Vet 2
        vet2 = User.objects.create_user(
            username='dragomez', email='gomez@vetcore.local', password='vet1234',
            first_name='Lucía', last_name='Gómez'
        )
        vet2_profile = UserProfile.objects.create(
            user=vet2, company=company, role='VET',
            is_admin=False, license_number='MP-7832', pin='2222',
            avatar='bi-emoji-smile-fill'
        )

        return admin_user, vet1, vet2, admin_profile, vet1_profile, vet2_profile

    def _create_clients_patients(self, company):
        clients_data = [
            ('Juan', 'Pérez', '351-6001001', 'juan.perez@email.com', 'Bv. San Juan 450'),
            ('María', 'González', '351-6002002', 'maria.gon@email.com', 'Av. Vélez Sarsfield 890'),
            ('Roberto', 'Fernández', '351-6003003', 'rfernandez@email.com', 'Caseros 1200'),
            ('Ana', 'Martínez', '351-6004004', 'ana.mtz@email.com', 'Dean Funes 320'),
            ('Carlos', 'Ruiz', '351-6005005', 'cruiz@email.com', 'Chacabuco 780'),
            ('Sofía', 'Torres', '351-6006006', 'sofia.t@email.com', 'Obispo Trejo 550'),
            ('Diego', 'Morales', '351-6007007', 'dmorales@email.com', 'Av. General Paz 2100'),
            ('Laura', 'Sánchez', '351-6008008', 'lsanchez@email.com', 'Humberto Primo 945'),
            ('Pablo', 'Romero', '351-6009009', 'promero@email.com', 'Santa Rosa 1350'),
            ('Valentina', 'Castro', '351-6010010', 'vcastro@email.com', 'Av. Sabattini 3200'),
            ('Martín', 'Díaz', '351-6011011', '', 'Jujuy 670'),
            ('Camila', 'López', '351-6012012', 'clopez@email.com', ''),
        ]

        pets_data = [
            # (client_idx, name, species, breed, birth_offset_days, weight)
            (0, 'Rocky', 'DOG', 'Labrador', 1200, Decimal('32.5')),
            (0, 'Luna', 'CAT', 'Siamés', 800, Decimal('4.2')),
            (1, 'Max', 'DOG', 'Pastor Alemán', 1800, Decimal('38.0')),
            (1, 'Michi', 'CAT', 'Mestizo', 600, Decimal('5.1')),
            (2, 'Toby', 'DOG', 'Beagle', 900, Decimal('12.8')),
            (3, 'Firulais', 'DOG', 'Caniche Toy', 2500, Decimal('3.9')),
            (3, 'Negra', 'CAT', 'Persa', 1500, Decimal('4.8')),
            (4, 'Thor', 'DOG', 'Rottweiler', 700, Decimal('42.0')),
            (5, 'Coco', 'DOG', 'French Poodle', 1100, Decimal('8.5')),
            (5, 'Simba', 'CAT', 'Bengalí', 400, Decimal('5.5')),
            (6, 'Rex', 'DOG', 'Dogo Argentino', 1000, Decimal('40.0')),
            (7, 'Pelusa', 'CAT', 'Angora', 1300, Decimal('3.7')),
            (8, 'Bruno', 'DOG', 'Golden Retriever', 500, Decimal('28.0')),
            (9, 'Kiara', 'DOG', 'Border Collie', 850, Decimal('18.5')),
            (10, 'Tito', 'DOG', 'Mestizo', 2000, Decimal('15.0')),
            (10, 'Manchas', 'CAT', 'Mestizo', 700, Decimal('4.0')),
            (11, 'Lola', 'DOG', 'Bulldog Francés', 650, Decimal('11.2')),
            (11, 'Copito', 'OTHER', 'Conejo Enano', 300, Decimal('1.8')),
        ]

        clients = []
        for first_name, last_name, tel, email, address in clients_data:
            c = Client.objects.create(
                company=company, first_name=first_name, last_name=last_name,
                phone=tel, email=email or None, address=address,
            )
            clients.append(c)

        patients = []
        today = date.today()
        for cli_idx, name, species, breed, days, weight in pets_data:
            p = Patient.objects.create(
                company=company, owner=clients[cli_idx],
                name=name, species=species, breed=breed,
                birth_date=today - timedelta(days=days),
                current_weight=weight,
            )
            patients.append(p)

        return clients, patients

    def _create_medical_records(self, patients):
        records_data = [
            ('Vacunación Antirrábica', 'Paciente en buen estado general', 'Rabia: vacuna aplicada', 'Refuerzo anual'),
            ('Vacunación Quíntuple', 'Sin signos clínicos', 'Vacuna quíntuple aplicada', 'Refuerzo en 21 días'),
            ('Control general', 'Propietario refiere que come bien', 'Paciente sano', 'Continuar alimentación actual'),
            ('Vómitos y diarrea', 'Vómitos desde hace 2 días, diarrea líquida', 'Gastroenteritis aguda', 'Dieta blanda 3 días + Metoclopramida 0.5mg/kg'),
            ('Castración', 'Paciente apto para cirugía, ayuno 12hs', 'Orquiectomía / OVH programada', 'Antibiótico 7 días + collar isabelino'),
            ('Desparasitación', 'Control rutinario', 'Desparasitación interna aplicada', 'Repetir en 3 meses'),
            ('Otitis', 'Se rasca la oreja derecha frecuentemente', 'Otitis externa por Malassezia', 'Gotas óticas 2 veces/día x 10 días'),
            ('Dermatitis', 'Lesiones en piel, prurito intenso', 'Dermatitis alérgica', 'Baños medicados + antihistamínico'),
            ('Cojera', 'Cojea del miembro anterior izquierdo', 'Esguince leve', 'Reposo 5 días + antiinflamatorio'),
            ('Limpieza dental', 'Sarro moderado, halitosis', 'Enfermedad periodontal grado II', 'Limpieza ultrasónica realizada'),
        ]

        now = timezone.now()
        for patient in patients:
            n_records = random.randint(1, 4)
            selection = random.sample(records_data, min(n_records, len(records_data)))
            for i, (reason, anam, diag, treat) in enumerate(selection):
                days_ago = random.randint(5, 180)
                MedicalRecord.objects.create(
                    patient=patient,
                    date=now - timedelta(days=days_ago),
                    reason=reason,
                    anamnesis=anam,
                    diagnosis=diag,
                    treatment=treat,
                    weight=patient.current_weight,
                )

    def _create_appointments(self, company, patients, vets):
        appointment_reasons = [
            'Vacunación', 'Control post-quirúrgico', 'Desparasitación',
            'Control general', 'Castración', 'Limpieza dental',
            'Revisión de piel', 'Control de peso', 'Extracción de sangre',
        ]

        now = timezone.now()
        today = now.date()

        # Past appointments (COMPLETED)
        for i in range(6):
            pat = random.choice(patients)
            vet = random.choice(vets)
            day = today - timedelta(days=random.randint(1, 30))
            hour = random.choice([9, 10, 11, 14, 15, 16, 17])
            start = timezone.make_aware(
                timezone.datetime(day.year, day.month, day.day, hour, 0)
            )
            Appointment.objects.create(
                company=company, patient=pat, professional=vet,
                start_time=start,
                end_time=start + timedelta(minutes=30),
                reason=random.choice(appointment_reasons),
                status='COMPLETED',
            )

        # Future appointments (PENDING and CONFIRMED)
        for i in range(8):
            pat = random.choice(patients)
            vet = random.choice(vets)
            day = today + timedelta(days=random.randint(1, 14))
            hour = random.choice([9, 10, 11, 14, 15, 16, 17])
            start = timezone.make_aware(
                timezone.datetime(day.year, day.month, day.day, hour, 0)
            )
            Appointment.objects.create(
                company=company, patient=pat, professional=vet,
                start_time=start,
                end_time=start + timedelta(minutes=30),
                reason=random.choice(appointment_reasons),
                status=random.choice(['PENDING', 'CONFIRMED']),
            )

        # One cancelled appointment
        pat = random.choice(patients)
        vet = random.choice(vets)
        day = today + timedelta(days=2)
        start = timezone.make_aware(
            timezone.datetime(day.year, day.month, day.day, 11, 0)
        )
        Appointment.objects.create(
            company=company, patient=pat, professional=vet,
            start_time=start,
            end_time=start + timedelta(minutes=30),
            reason='Vacunación',
            status='CANCELLED',
            notes='Cancelled by client',
        )

    def _create_products(self, company):
        products_data = [
            # (description, type, barcode, cost, sale_price, stock, min_stock)
            ('Vacuna Antirrábica', 'PRODUCT', '7790001001', 3500, 6000, 20, 5),
            ('Vacuna Quíntuple Canina', 'PRODUCT', '7790001002', 4200, 7500, 15, 5),
            ('Vacuna Triple Felina', 'PRODUCT', '7790001003', 3800, 6500, 12, 5),
            ('Antiparasitario Interno (comp.)', 'PRODUCT', '7790002001', 1200, 2500, 50, 10),
            ('Pipeta Antipulgas Perro Grande', 'PRODUCT', '7790002002', 2800, 5000, 30, 8),
            ('Pipeta Antipulgas Gato', 'PRODUCT', '7790002003', 2200, 4000, 25, 8),
            ('Amoxicilina 500mg (caja x20)', 'PRODUCT', '7790003001', 1800, 3200, 18, 5),
            ('Metoclopramida gotas', 'PRODUCT', '7790003002', 900, 1800, 10, 3),
            ('Collar Isabelino M', 'PRODUCT', '7790004001', 1500, 3000, 8, 3),
            ('Collar Isabelino L', 'PRODUCT', '7790004002', 1800, 3500, 6, 3),
            ('Alimento Balanceado Perro 15kg', 'PRODUCT', '7790005001', 18000, 28000, 10, 3),
            ('Alimento Balanceado Gato 7.5kg', 'PRODUCT', '7790005002', 14000, 22000, 8, 3),
            ('Shampoo Medicado 250ml', 'PRODUCT', '7790006001', 2500, 4500, 12, 4),
            ('Gotas Óticas 20ml', 'PRODUCT', '7790006002', 1100, 2200, 15, 5),
            ('Suero Fisiológico 500ml', 'PRODUCT', '7790007001', 800, 1500, 20, 5),
            # Services
            ('Consulta General', 'SERVICE', None, 0, 8000, 0, 0),
            ('Castración Macho (hasta 10kg)', 'SERVICE', None, 0, 25000, 0, 0),
            ('Castración Hembra (hasta 10kg)', 'SERVICE', None, 0, 35000, 0, 0),
            ('Limpieza Dental con Ultrasonido', 'SERVICE', None, 0, 18000, 0, 0),
            ('Cirugía Menor', 'SERVICE', None, 0, 30000, 0, 0),
            ('Radiografía', 'SERVICE', None, 0, 12000, 0, 0),
            ('Ecografía Abdominal', 'SERVICE', None, 0, 15000, 0, 0),
            ('Análisis de Sangre Completo', 'SERVICE', None, 0, 10000, 0, 0),
        ]

        products = []
        for desc, ptype, barcode, cost, price, stock, min_stock in products_data:
            p = Product.objects.create(
                company=company,
                description=desc,
                type=ptype,
                barcode=barcode,
                cost=Decimal(str(cost)),
                sale_price=Decimal(str(price)),
                current_stock=stock,
                minimum_stock=min_stock,
            )
            products.append(p)

        return products

    def _create_sales(self, company, clients, products, user):
        now = timezone.now()
        methods = ['CASH', 'CARD', 'TRANSFER', 'QR']

        physical = [p for p in products if p.type == 'PRODUCT']
        services = [p for p in products if p.type == 'SERVICE']

        for i in range(15):
            days_ago = random.randint(0, 30)
            sale_date = now - timedelta(days=days_ago, hours=random.randint(0, 8))

            client = random.choice(clients) if random.random() > 0.2 else None
            method = random.choice(methods)

            sale = Sale.objects.create(
                company=company,
                date=sale_date,
                client=client,
                payment_method=method,
                total=0,
            )

            total = Decimal('0')
            n_items = random.randint(1, 4)

            items_pool = random.sample(physical, min(n_items, len(physical)))
            if random.random() > 0.5 and services:
                items_pool.append(random.choice(services))

            for prod in items_pool:
                qty = random.randint(1, 3) if prod.type == 'PRODUCT' else 1
                subtotal = prod.sale_price * qty
                total += subtotal

                SaleItem.objects.create(
                    sale=sale,
                    product=prod,
                    quantity=qty,
                    unit_price=prod.sale_price,
                    subtotal=subtotal,
                )

            sale.total = total
            sale.save()
