"""
Vetter (FoxPro) → VetCoreSoft migration service.

Reads .DBF files from a Vetter data directory and imports clients, patients,
clinical history, products, sales and vaccine records into the current company.
"""
import os
import re
import logging
from datetime import datetime, date
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone

from dbfread import DBF

from core.models import Company, Client, Patient
from clinical.models import MedicalRecord, Appointment
from inventory.models import Product, StockMovement
from sales.models import Sale, SaleItem

logger = logging.getLogger(__name__)

# ─── Species mapping ───────────────────────────────────────────────
SPECIES_MAP = {
    'CANINO': 'DOG',
    'FELINO': 'CAT',
    'EQUINO': 'HORSE',
}

# ─── Sex mapping ───────────────────────────────────────────────────
SEX_MAP = {
    'MACHO': 'M',
    'HEMBRA': 'F',
    'MACHO CASTRADO': 'M',
    'HEMBRA CASTRADA': 'F',
}

# ─── Payment method mapping ───────────────────────────────────────
PAYMENT_MAP = {
    'EFECTIVO': 'CASH',
    'TARJETA': 'CARD',
    'TRANSFERENCIA': 'TRANSFER',
    'QR': 'QR',
}


def _read_dbf(data_dir, filename):
    """Read a DBF file with latin-1 encoding, case-insensitive file lookup."""
    # DBF filenames may have mixed case on disk
    for name in os.listdir(data_dir):
        if name.upper() == filename.upper():
            path = os.path.join(data_dir, name)
            return list(DBF(path, encoding='latin-1', ignore_missing_memofile=True))
    return []


def _safe_str(val, max_len=None):
    """Clean a string value from DBF."""
    if val is None:
        return ''
    s = str(val).strip()
    if max_len:
        s = s[:max_len]
    return s


def _safe_date(val):
    """Convert a DBF date to a Python date, or None."""
    if isinstance(val, date):
        return val
    return None


def _safe_decimal(val, default=Decimal('0')):
    """Convert a numeric value to Decimal."""
    try:
        return Decimal(str(val)) if val else default
    except (InvalidOperation, ValueError):
        return default


def _parse_client_name(full_name):
    """
    Parse 'LAST_NAME FIRST_NAME' into (last_name, first_name).
    Vetter stores names as single field. We split on last space or use full as last_name.
    """
    full_name = _safe_str(full_name)
    if not full_name:
        return ('Sin Nombre', '')
    parts = full_name.split()
    if len(parts) == 1:
        return (parts[0].title(), '')
    # First word = last name, rest = first name
    return (parts[0].title(), ' '.join(parts[1:]).title())


def _parse_clinica_entries(descrip_text):
    """
    Parse the concatenated clinical history text from CLINICA.DESCRIP.
    Each entry starts with: ******  Fecha: DD/MM/YYYY HH:MM:SS AM/PM -- Atendido Por: VET_NAME
    Returns list of dicts with 'date', 'vet_name', 'body'.
    """
    if not descrip_text:
        return []

    # Split by the entry delimiter
    pattern = r'\*{4,}\s+Fecha:\s*'
    parts = re.split(pattern, descrip_text)
    entries = []

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Try to parse: DD/MM/YYYY HH:MM:SS AM/PM -- Atendido Por: VET_NAME\nbody
        header_match = re.match(
            r'(\d{1,2}/\d{1,2}/\d{4})\s+'
            r'(\d{1,2}:\d{2}:\d{2}\s*(?:AM|PM)?)\s*'
            r'--\s*Atendido\s+Por:\s*(.+?)$',
            part,
            re.MULTILINE | re.IGNORECASE,
        )

        if header_match:
            date_str = header_match.group(1)
            time_str = header_match.group(2).strip()
            vet_name = header_match.group(3).strip()
            body = part[header_match.end():].strip()

            # Parse date
            try:
                dt_str = f"{date_str} {time_str}"
                for fmt in ('%d/%m/%Y %I:%M:%S %p', '%d/%m/%Y %H:%M:%S %p',
                            '%d/%m/%Y %H:%M:%S', '%d/%m/%Y'):
                    try:
                        dt = datetime.strptime(dt_str.strip(), fmt)
                        break
                    except ValueError:
                        continue
                else:
                    dt = datetime.strptime(date_str, '%d/%m/%Y')
            except ValueError:
                dt = datetime.now()

            entries.append({
                'date': timezone.make_aware(dt) if timezone.is_naive(dt) else dt,
                'vet_name': vet_name,
                'body': body,
            })
        else:
            # Could not parse header — store as-is with current date
            entries.append({
                'date': timezone.now(),
                'vet_name': '',
                'body': part,
            })

    return entries


class VetterImporter:
    """
    Imports data from a Vetter (FoxPro) data directory into VetCoreSoft.
    """

    def __init__(self, data_dir, company):
        self.data_dir = data_dir
        self.company = company
        self.log = []
        self.stats = {
            'clients': 0,
            'patients': 0,
            'records': 0,
            'vaccines': 0,
            'products': 0,
            'sales': 0,
            'errors': [],
        }
        # Maps for cross-referencing: vetter_code → django object
        self._client_map = {}    # vetter CODIGO → Client
        self._patient_map = {}   # vetter CODIGOPACI → Patient
        self._product_map = {}   # vetter ID_ART → Product

    # DBF file → table key mapping
    TABLE_FILES = {
        'clients': 'CLIENTES.DBF',
        'patients': 'pacientes.dbf',
        'records': 'CLINICA.DBF',
        'vaccines': 'VACUNAS.DBF',
        'products': 'STOCK.DBF',
        'sales': 'ENTRADAS.DBF',
    }

    # Dependencies: key requires all values to be selected too
    TABLE_DEPS = {
        'patients': ['clients'],
        'records': ['clients', 'patients'],
        'vaccines': ['clients', 'patients'],
        'sales': ['clients'],
    }

    def validate(self):
        """Check that the directory contains valid Vetter data."""
        if not os.path.isdir(self.data_dir):
            return False, "Directory does not exist."

        required = ['CLIENTES.DBF', 'pacientes.dbf']
        found = {f.upper() for f in os.listdir(self.data_dir) if f.upper().endswith('.DBF')}
        missing = [r for r in required if r.upper() not in found]
        if missing:
            return False, f"Missing required files: {', '.join(missing)}"

        return True, "Valid Vetter data directory."

    def analyze(self):
        """Return record counts per table without importing anything."""
        counts = {}
        for key, filename in self.TABLE_FILES.items():
            try:
                rows = _read_dbf(self.data_dir, filename)
                counts[key] = len(rows)
            except Exception:
                counts[key] = -1  # file not found or error
        return counts

    ALL_TABLES = {'clients', 'patients', 'records', 'vaccines', 'products', 'sales'}

    @transaction.atomic
    def run(self, tables=None):
        """Execute the import for the selected tables (default: all)."""
        selected = set(tables) & self.ALL_TABLES if tables else self.ALL_TABLES

        self._log("Starting Vetter import...")
        self._log(f"  Data directory: {self.data_dir}")
        self._log(f"  Company: {self.company.name}")
        self._log(f"  Tables: {', '.join(sorted(selected))}")

        if 'clients' in selected:
            self._import_clients()
        if 'patients' in selected:
            self._import_patients()
        if 'records' in selected:
            self._import_clinical_records()
        if 'vaccines' in selected:
            self._import_vaccines()
        if 'products' in selected:
            self._import_products()
        if 'sales' in selected:
            self._import_sales()

        self._log(f"\n{'='*40}")
        self._log(f"Import completed!")
        self._log(f"  Clients:  {self.stats['clients']}")
        self._log(f"  Patients: {self.stats['patients']}")
        self._log(f"  Records:  {self.stats['records']}")
        self._log(f"  Vaccines: {self.stats['vaccines']}")
        self._log(f"  Products: {self.stats['products']}")
        self._log(f"  Sales:    {self.stats['sales']}")
        if self.stats['errors']:
            self._log(f"  Errors:   {len(self.stats['errors'])}")

        return self.stats, self.log

    def _log(self, msg):
        self.log.append(msg)
        logger.info(f"[VetterImport] {msg}")

    def _import_clients(self):
        self._log("\n📋 Importing clients...")
        rows = _read_dbf(self.data_dir, 'CLIENTES.DBF')
        for row in rows:
            if row.get('ANULADO'):
                continue
            code = int(row.get('CODIGO', 0))
            if code == 0:
                continue

            last_name, first_name = _parse_client_name(row.get('NOMBRE', ''))
            phone_parts = []
            if _safe_str(row.get('TELEFONO')):
                phone_parts.append(_safe_str(row['TELEFONO']))
            if _safe_str(row.get('SMS')):
                phone_parts.append(_safe_str(row['SMS']))

            client = Client.objects.create(
                company=self.company,
                last_name=last_name,
                first_name=first_name,
                phone=', '.join(phone_parts)[:50] if phone_parts else '',
                email=_safe_str(row.get('EMAIL')) or None,
                address=_safe_str(row.get('DIRECCION'), 255),
                city=_safe_str(row.get('LOCALIDAD'), 100),
                province=_safe_str(row.get('PROVINCIA'), 100),
                notes=_safe_str(row.get('DATOS_FAC')),
            )
            self._client_map[code] = client
            self.stats['clients'] += 1

        self._log(f"  → {self.stats['clients']} clients imported")

    def _import_patients(self):
        self._log("\n🐾 Importing patients...")
        rows = _read_dbf(self.data_dir, 'pacientes.dbf')
        for row in rows:
            if row.get('ANULADO'):
                continue

            code = int(row.get('CODIGO', 0))
            codigopaci = _safe_str(row.get('CODIGOPACI'))
            if not codigopaci:
                continue

            owner = self._client_map.get(code)
            if not owner:
                self.stats['errors'].append(f"Patient {codigopaci}: owner {code} not found")
                continue

            especie = _safe_str(row.get('ESPECIE', '')).upper()
            species = SPECIES_MAP.get(especie, 'OTHER')

            sexo = _safe_str(row.get('SEXO', '')).upper()
            sex = SEX_MAP.get(sexo, 'U')

            patient = Patient.objects.create(
                company=self.company,
                owner=owner,
                name=_safe_str(row.get('NOMBRE', 'Sin Nombre'), 100).title(),
                species=species,
                breed=_safe_str(row.get('RAZA', ''), 100).title(),
                sex=sex,
                birth_date=_safe_date(row.get('FECHA_NAC')),
                microchip=_safe_str(row.get('MICROCHIP'), 50),
                coat=_safe_str(row.get('PELAJE'), 50).title(),
                is_alive=row.get('VIVE', True),
            )
            self._patient_map[codigopaci] = patient
            self.stats['patients'] += 1

        self._log(f"  → {self.stats['patients']} patients imported")

    def _import_clinical_records(self):
        self._log("\n📝 Importing clinical records...")
        rows = _read_dbf(self.data_dir, 'CLINICA.DBF')
        for row in rows:
            codigopaci = _safe_str(row.get('CODIGOPACI'))
            patient = self._patient_map.get(codigopaci)
            if not patient:
                continue

            descrip = row.get('DESCRIP', '')
            entries = _parse_clinica_entries(descrip)

            for entry in entries:
                body = entry['body']
                if not body or len(body.strip()) < 3:
                    continue

                MedicalRecord.objects.create(
                    patient=patient,
                    date=entry['date'],
                    reason='Consulta (migrado de Vetter)',
                    anamnesis=body,
                    vet_name=_safe_str(entry['vet_name'], 100),
                )
                self.stats['records'] += 1

        self._log(f"  → {self.stats['records']} clinical records imported")

    def _import_vaccines(self):
        self._log("\n💉 Importing vaccine records...")
        rows = _read_dbf(self.data_dir, 'VACUNAS.DBF')
        for row in rows:
            if row.get('CANCELADA'):
                continue

            codigopaci = _safe_str(row.get('CODIGOPACI'))
            patient = self._patient_map.get(codigopaci)
            if not patient:
                continue

            vaccine_name = _safe_str(row.get('VACUNA', ''))
            marca = _safe_str(row.get('MARCA', ''))
            fecha_apli = _safe_date(row.get('FECHA_APLI'))
            fecha_reva = _safe_date(row.get('FECHA_REVA'))

            treatment = f"Vacuna: {vaccine_name}"
            if marca:
                treatment += f" | Marca: {marca}"
            if fecha_reva:
                treatment += f" | Revacunación: {fecha_reva.strftime('%d/%m/%Y')}"

            dt = timezone.make_aware(
                datetime.combine(fecha_apli, datetime.min.time())
            ) if fecha_apli else timezone.now()

            MedicalRecord.objects.create(
                patient=patient,
                date=dt,
                reason=f'Vacunación: {vaccine_name}',
                treatment=treatment,
                next_visit=fecha_reva,
            )
            self.stats['vaccines'] += 1

        self._log(f"  → {self.stats['vaccines']} vaccine records imported")

    def _import_products(self):
        self._log("\n📦 Importing products...")
        rows = _read_dbf(self.data_dir, 'STOCK.DBF')
        for row in rows:
            id_art = int(row.get('ID_ART', 0))
            descripcion = _safe_str(row.get('ARTICULO', ''))
            if not descripcion:
                continue

            tipo_str = _safe_str(row.get('TIPO', '')).upper()
            is_service = 'HONORARIO' in tipo_str or 'SERVICIO' in tipo_str
            ptype = 'SERVICE' if is_service else 'PRODUCT'

            barcode = _safe_str(row.get('CODIGO'), 50) or None
            # Avoid duplicate barcodes
            if barcode and Product.objects.filter(barcode=barcode).exists():
                barcode = None

            product = Product.objects.create(
                company=self.company,
                barcode=barcode,
                description=descripcion[:200],
                type=ptype,
                cost=_safe_decimal(row.get('COSTO')),
                sale_price=_safe_decimal(row.get('PRECIO', 0)),
                current_stock=max(int(_safe_decimal(row.get('STOCK', 0))), 0),
                minimum_stock=max(int(_safe_decimal(row.get('STOCK_MIN', 0))), 0),
            )
            self._product_map[id_art] = product
            self.stats['products'] += 1

        self._log(f"  → {self.stats['products']} products imported")

    def _import_sales(self):
        self._log("\n💰 Importing sales (ENTRADAS)...")
        rows = _read_dbf(self.data_dir, 'ENTRADAS.DBF')

        # Group entries by date + client to create single sales
        from collections import defaultdict
        daily_sales = defaultdict(list)

        for row in rows:
            fecha = _safe_date(row.get('FECHA'))
            if not fecha:
                continue
            id_cliente = int(row.get('ID_CLIENTE', 0))
            # Group by date + client
            key = (fecha, id_cliente)
            daily_sales[key].append(row)

        for (fecha, id_cliente), items in daily_sales.items():
            client = self._client_map.get(id_cliente)  # May be None for walk-ins

            forma = _safe_str(items[0].get('FORMA1', 'EFECTIVO')).upper()
            payment = PAYMENT_MAP.get(forma, 'CASH')

            dt = timezone.make_aware(datetime.combine(fecha, datetime.min.time()))

            sale = Sale.objects.create(
                company=self.company,
                date=dt,
                client=client,
                payment_method=payment,
                total=Decimal('0'),
            )

            total = Decimal('0')
            for item in items:
                cantidad = max(int(_safe_decimal(item.get('CANTIDAD', 1))), 1)
                importe = _safe_decimal(item.get('IMPORTE', 0))
                precio_unit = importe / cantidad if cantidad > 0 else importe
                subtotal = importe

                id_art = int(item.get('ID_ART', 0))
                product = self._product_map.get(id_art)

                if not product:
                    # Create a generic product for unmapped items
                    desc = _safe_str(item.get('DESCRIP', 'Artículo migrado'))
                    product = Product.objects.create(
                        company=self.company,
                        description=desc[:200],
                        type='PRODUCT',
                        sale_price=precio_unit,
                        current_stock=0,
                        minimum_stock=0,
                    )
                    if id_art > 0:
                        self._product_map[id_art] = product

                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=cantidad,
                    unit_price=precio_unit,
                    subtotal=subtotal,
                )
                total += subtotal

            sale.total = total
            sale.save(update_fields=['total'])
            self.stats['sales'] += 1

        self._log(f"  → {self.stats['sales']} sales imported")
