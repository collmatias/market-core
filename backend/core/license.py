import uuid
import hashlib
import os
import json
import requests # <--- Necesario para hablar con AWS
from datetime import datetime, timedelta
from django.conf import settings

# --- CONFIGURACIÓN ---
SECRET_SALT = "VETCORE_PROTECTED_BY_MATIAS_2026_X99"
LICENSE_FILE = os.path.join(settings.BASE_DIR, 'license.key')
CACHE_FILE = os.path.join(settings.BASE_DIR, 'license_cache.json')

# ENTORNO DE DESARROLLO (Docker / Local)
DEBUG_URL = "http://cloud_api:8000/check-license"

# ENTORNO DE PRODUCCIÓN (El dominio real que comprarás)
# Cuando compiles el .exe, Python no tendrá la variable de entorno de Docker,
# así que usará esta por defecto o una lógica de fallback.
PRODUCTION_URL = "https://api.vetcore.com.ar/check-license" 

# LÓGICA DE SELECCIÓN
# Si estamos dentro de Docker (tu entorno dev), usamos la local.
# Si no (es el .exe en Windows del cliente), usamos la de producción.
if os.environ.get('AM_I_IN_DOCKER'):
    AWS_LAMBDA_URL = os.environ.get('LICENSE_API_URL', DEBUG_URL)
else:
    # AQUÍ ES DONDE APUNTARÁ EL EXE FINAL
    AWS_LAMBDA_URL = PRODUCTION_URL

def get_hardware_id():
    """
    Obtiene un ID único.
    - En PROD (Windows): Usa la MAC Address real.
    - En DEV (Docker): Usa un ID fijo para no tener que reactivar a cada rato.
    """
    
    # Si existe la variable VETCORE_MODE (que solo pusimos en el docker-compose),
    # asumimos que es entorno de desarrollo.
    if os.environ.get('VETCORE_MODE'):
        # Retornamos un ID fijo cualquiera (ej: puros nueves)
        return "999999999999"
    
    # Lógica Real para Producción (.exe)
    mac = uuid.getnode()
    return str(mac)

def generate_offline_key(hardware_id):
    """Genera la clave matemática para licencias PERPETUAS"""
    raw_string = f"{hardware_id}|{SECRET_SALT}"
    hash_object = hashlib.sha256(raw_string.encode())
    return hash_object.hexdigest()[:16].upper()

def check_online_status(hardware_id):
    """
    Consulta a AWS si la suscripción está activa.
    Retorna: (EsValido, FechaVencimiento, Mensaje)
    """
    try:
        response = requests.post(AWS_LAMBDA_URL, json={'hw_id': hardware_id}, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            # data = {'status': 'ACTIVE', 'expires': '2026-03-01'}
            
            if data.get('status') == 'ACTIVE':
                # Guardamos en caché local para no preguntar cada segundo
                update_local_cache(True, data.get('expires'))
                return True, "Suscripción Activa"
            else:
                update_local_cache(False, None)
                return False, "Suscripción Vencida o Impaga"
        else:
            # Si el servidor da error, usamos el caché (Grace Period)
            return check_local_cache()
            
    except requests.exceptions.RequestException:
        # Sin internet: Usamos el caché (Grace Period)
        return check_local_cache()

def update_local_cache(is_active, expiration_date):
    """Guarda el estado para cuando no haya internet"""
    data = {
        'last_check': datetime.now().isoformat(),
        'is_active': is_active,
        'expiration_date': expiration_date
    }
    with open(CACHE_FILE, 'w') as f:
        json.dump(data, f)

def check_local_cache():
    """Verifica si todavía estamos en el periodo de gracia offline"""
    if not os.path.exists(CACHE_FILE):
        return False, "Sin conexión y sin caché previo"
        
    try:
        with open(CACHE_FILE, 'r') as f:
            data = json.load(f)
            
        # Si la última vez que chequeamos estaba activo...
        if data['is_active']:
            # Damos 3 días de gracia sin internet
            last_check = datetime.fromisoformat(data['last_check'])
            if datetime.now() - last_check < timedelta(days=3):
                return True, "Modo Offline (Gracia)"
                
        return False, "No se pudo verificar la licencia"
    except (json.JSONDecodeError, KeyError, ValueError, OSError):
        return False, "Error de caché"

def check_license():
    """
    Lógica Maestra:
    1. Revisa si hay archivo de licencia.
    2. Si empieza con 'SUB-', es Online.
    3. Si no, es Perpetua (Offline).
    """
    current_hw_id = get_hardware_id()
    
    if not os.path.exists(LICENSE_FILE):
        return False, current_hw_id

    try:
        with open(LICENSE_FILE, 'r') as f:
            stored_key = f.read().strip()

        # CASO A: LICENCIA ONLINE (Suscripción)
        # Tú decidirás que las claves online empiecen con "SUB-"
        if stored_key.startswith("SUB-"):
            is_valid, msg = check_online_status(current_hw_id)
            return is_valid, current_hw_id

        # CASO B: LICENCIA PERPETUA (Offline)
        expected_key = generate_offline_key(current_hw_id)
        if stored_key == expected_key:
            return True, current_hw_id
        else:
            return False, current_hw_id
            
    except (OSError, ValueError, KeyError):
        return False, current_hw_id

def save_license(key):
    with open(LICENSE_FILE, 'w') as f:
        f.write(key.strip())