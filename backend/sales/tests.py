from django.test import TestCase, Client
from django.contrib.auth.models import User
from inventory.models import Producto, MovimientoStock
from core.models import Cliente
from sales.models import Venta
import json

class VentaFlowTest(TestCase):
    def setUp(self):
        # 1. Crear un usuario para loguearse
        self.user = User.objects.create_user(username='testvet', password='123')
        self.client = Client()
        self.client.login(username='testvet', password='123')

        # 2. Crear Cliente
        self.cliente = Cliente.objects.create(nombre="Juan", apellido="Perez", telefono="111")
        
        # 3. Crear Producto
        self.producto = Producto.objects.create(
            descripcion="Vacuna Rabia",
            codigo_barras="VAC001",
            costo=1000,
            precio_venta=2000
            # cantidad_actual empieza en 0 por defecto según tu modelo
        )

        # 4. Cargar Stock Inicial
        # --- CORRECCIONES APLICADAS ---
        MovimientoStock.objects.create(
            producto=self.producto,
            tipo='ENTRADA',    # Nombre correcto: 'tipo'
            cantidad=10,
            usuario=self.user
            # Eliminamos 'motivo' porque no existe en tu modelo
        )

    def test_venta_descuenta_stock(self):
        """Prueba que una venta reduce el stock y calcula el total"""
        
        # Simulamos el carrito
        carrito = [
            {
                'id': self.producto.id,
                'cantidad': 2,
                'precio': 2000
            }
        ]

        # Hacemos el POST
        response = self.client.post('/caja/', {
            'cliente': self.cliente.id,
            'metodo_pago': 'EFECTIVO',
            'carrito_data': json.dumps(carrito)
        }, follow=True)

        # Verificaciones
        self.assertEqual(response.status_code, 200)
        
        # 1. Chequear Total Venta
        venta = Venta.objects.last()
        self.assertEqual(venta.total, 4000)

        # 2. Chequear Stock
        self.producto.refresh_from_db() 
        # --- CORRECCIÓN APLICADA ---
        # Tu campo se llama 'cantidad_actual', no 'stock'
        self.assertEqual(self.producto.cantidad_actual, 8)