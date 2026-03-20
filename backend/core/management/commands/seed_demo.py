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

from core.models import Company, UserProfile, Client
from inventory.models import Product, StockMovement
from sales.models import Sale, SaleItem


class Command(BaseCommand):
    help = 'Wipes the DB and loads realistic demo data for a retail store'

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
        admin_user, cashier1, cashier2 = self._create_users(company)

        self.stdout.write('🧑 Creating clients...')
        clients = self._create_clients(company)

        self.stdout.write('📦 Creating products...')
        products = self._create_products(company)

        self.stdout.write('💰 Creating sales...')
        self._create_sales(company, clients, products, admin_user)

        self.stdout.write(self.style.SUCCESS('\n✅ Demo data loaded successfully!'))
        self.stdout.write(self.style.SUCCESS('─' * 50))
        self.stdout.write(f'   🏢 Company: {company.name}')
        self.stdout.write(f'   👤 Admin: admin / admin1234')
        self.stdout.write(f'   💵 Cashier 1: cajero1 / caja1234')
        self.stdout.write(f'   💵 Cashier 2: cajero2 / caja1234')
        self.stdout.write(f'   🧑 Clients: {len(clients)}')
        self.stdout.write(f'   📦 Products: {len(products)}')
        self.stdout.write(self.style.SUCCESS('─' * 50))

    def _flush(self):
        """Delete all data in safe order (respecting FK constraints)."""
        SaleItem.objects.all().delete()
        Sale.objects.all().delete()
        StockMovement.objects.all().delete()
        Product.objects.all().delete()
        Client.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.all().delete()
        Company.objects.all().delete()

    def _create_company(self):
        return Company.objects.create(
            name='Almacén Don Pedro',
            tax_id='30-71234567-9',
            address='Av. Colón 1234, Córdoba',
            phone='351-4567890',
            plan='TRIAL',
            expiration_date=date.today() + timedelta(days=90),
            is_active=True,
        )

    def _create_users(self, company):
        admin_user = User.objects.create_superuser(
            username='admin', email='admin@marketcore.local', password='admin1234',
            first_name='Pedro', last_name='Administrador'
        )
        UserProfile.objects.create(
            user=admin_user, company=company, role='ADMIN',
            is_admin=True, pin='0000', avatar='bi-person-fill'
        )

        cashier1 = User.objects.create_user(
            username='cajero1', email='cajero1@marketcore.local', password='caja1234',
            first_name='Carlos', last_name='López'
        )
        UserProfile.objects.create(
            user=cashier1, company=company, role='CASHIER',
            is_admin=False, pin='1111', avatar='bi-emoji-smile-fill'
        )

        cashier2 = User.objects.create_user(
            username='cajero2', email='cajero2@marketcore.local', password='caja1234',
            first_name='Lucía', last_name='Gómez'
        )
        UserProfile.objects.create(
            user=cashier2, company=company, role='CASHIER',
            is_admin=False, pin='2222', avatar='bi-emoji-sunglasses-fill'
        )

        return admin_user, cashier1, cashier2

    def _create_clients(self, company):
        clients_data = [
            ('Juan', 'Pérez', '351-6001001', 'juan.perez@email.com', 'Bv. San Juan 450', 'Córdoba', 'Córdoba'),
            ('María', 'González', '351-6002002', 'maria.gon@email.com', 'Av. Vélez Sarsfield 890', 'Córdoba', 'Córdoba'),
            ('Roberto', 'Fernández', '351-6003003', 'rfernandez@email.com', 'Caseros 1200', 'Córdoba', 'Córdoba'),
            ('Ana', 'Martínez', '351-6004004', 'ana.mtz@email.com', 'Dean Funes 320', 'Villa María', 'Córdoba'),
            ('Carlos', 'Ruiz', '351-6005005', 'cruiz@email.com', 'Chacabuco 780', 'Córdoba', 'Córdoba'),
            ('Sofía', 'Torres', '351-6006006', 'sofia.t@email.com', 'Obispo Trejo 550', 'Córdoba', 'Córdoba'),
            ('Diego', 'Morales', '351-6007007', 'dmorales@email.com', 'Av. General Paz 2100', 'Río Cuarto', 'Córdoba'),
            ('Laura', 'Sánchez', '351-6008008', 'lsanchez@email.com', 'Humberto Primo 945', 'Córdoba', 'Córdoba'),
            ('Pablo', 'Romero', '351-6009009', 'promero@email.com', 'Santa Rosa 1350', 'Córdoba', 'Córdoba'),
            ('Valentina', 'Castro', '351-6010010', 'vcastro@email.com', 'Av. Sabattini 3200', 'Córdoba', 'Córdoba'),
            ('Martín', 'Díaz', '351-6011011', '', 'Jujuy 670', 'Córdoba', 'Córdoba'),
            ('Camila', 'López', '351-6012012', 'clopez@email.com', '', '', ''),
        ]

        clients = []
        for first_name, last_name, tel, email, address, city, province in clients_data:
            c = Client.objects.create(
                company=company, first_name=first_name, last_name=last_name,
                phone=tel, email=email or None, address=address,
                city=city, province=province,
            )
            clients.append(c)

        return clients

    def _create_products(self, company):
        products_data = [
            # (description, type, barcode, cost, sale_price, stock, min_stock)
            ('Aceite Girasol 1.5L', 'PRODUCT', '7790001001', 1800, 2800, 40, 10),
            ('Harina 000 1kg', 'PRODUCT', '7790001002', 600, 1100, 60, 15),
            ('Azúcar 1kg', 'PRODUCT', '7790001003', 700, 1200, 50, 15),
            ('Arroz Largo Fino 1kg', 'PRODUCT', '7790002001', 800, 1400, 45, 10),
            ('Fideos Tallarines 500g', 'PRODUCT', '7790002002', 500, 900, 55, 12),
            ('Leche Entera 1L', 'PRODUCT', '7790002003', 900, 1500, 30, 10),
            ('Yerba Mate 1kg', 'PRODUCT', '7790003001', 2500, 4000, 35, 8),
            ('Café Molido 250g', 'PRODUCT', '7790003002', 2200, 3800, 20, 5),
            ('Gaseosa Cola 2.25L', 'PRODUCT', '7790004001', 1200, 2200, 25, 8),
            ('Agua Mineral 1.5L', 'PRODUCT', '7790004002', 500, 900, 40, 10),
            ('Pan Lactal 500g', 'PRODUCT', '7790005001', 1000, 1800, 20, 5),
            ('Galletitas Dulces 300g', 'PRODUCT', '7790005002', 800, 1500, 30, 8),
            ('Jabón en Polvo 800g', 'PRODUCT', '7790006001', 1500, 2800, 18, 5),
            ('Lavandina 1L', 'PRODUCT', '7790006002', 400, 800, 25, 8),
            ('Detergente 750ml', 'PRODUCT', '7790007001', 900, 1600, 22, 6),
            ('Papel Higiénico x4', 'PRODUCT', '7790007002', 1200, 2200, 20, 5),
            ('Huevos x12', 'PRODUCT', '7790008001', 2500, 4000, 15, 5),
            ('Queso Cremoso 1kg', 'PRODUCT', '7790008002', 5000, 8500, 8, 3),
            ('Jamón Cocido 1kg', 'PRODUCT', '7790008003', 6000, 10000, 6, 2),
            ('Carne Picada 1kg', 'PRODUCT', '7790009001', 4500, 7500, 10, 3),
            ('Pollo Entero 1kg', 'PRODUCT', '7790009002', 2800, 4500, 12, 4),
            ('Cerveza Lata 473ml', 'PRODUCT', '7790010001', 800, 1500, 50, 15),
            ('Vino Tinto 750ml', 'PRODUCT', '7790010002', 2000, 3500, 20, 5),
            # Services
            ('Envío a domicilio', 'SERVICE', None, 0, 1500, 0, 0),
            ('Carga de celular', 'SERVICE', None, 0, 500, 0, 0),
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
