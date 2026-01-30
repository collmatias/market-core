import socket

def get_server_ip():
    """Detecta la IP local de la máquina en la red (ej: 192.168.1.45)"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # No se conecta realmente, solo intenta para ver qué interfaz usa
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip