from django.test import TestCase, Client as TestClient
from django.contrib.auth.models import User
from core.models import Company, UserProfile, Client
from inventory.models import Product
from sales.models import Sale, SaleItem
from datetime import date, timedelta
from decimal import Decimal


class SaleModelTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name='Test Store', tax_id='30-00000000-0',
            plan='TRIAL', expiration_date=date.today() + timedelta(days=30),
            is_active=True,
        )
        self.user = User.objects.create_user(username='testcashier', password='123')
        UserProfile.objects.create(
            user=self.user, company=self.company, role='CASHIER', pin='0000',
        )
        self.client_record = Client.objects.create(
            company=self.company, first_name='Juan', last_name='Perez', phone='111',
        )
        self.product = Product.objects.create(
            company=self.company, description='Aceite Girasol 1.5L',
            barcode='7790001001', cost=Decimal('1800'),
            sale_price=Decimal('2800'), current_stock=10,
        )

    def test_sale_total_calculation(self):
        """A sale total equals the sum of its item subtotals."""
        sale = Sale.objects.create(
            company=self.company, client=self.client_record,
            payment_method='CASH', total=0,
        )
        SaleItem.objects.create(
            sale=sale, product=self.product, quantity=2,
            unit_price=self.product.sale_price,
            subtotal=self.product.sale_price * 2,
        )
        sale.total = sum(item.subtotal for item in sale.items.all())
        sale.save()

        sale.refresh_from_db()
        self.assertEqual(sale.total, Decimal('5600'))