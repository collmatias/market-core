"""
VetCoreSoft Desktop — Self-contained launcher for Windows.

Bundled with PyInstaller. Contains Python runtime + all dependencies.
The Django project lives in ./backend/ alongside this exe.

First run (with UAC elevation):
  - Adds 'vetcoresoft.local' to Windows hosts file
  - Generates self-signed SSL certificate and trusts it in Windows cert store
  - Creates a desktop shortcut with icon
  - Runs database migrations

Every run:
  - Starts Django HTTPS server on port 443
  - Opens the default browser to https://vetcoresoft.local
"""

import sys
import os
import ctypes
import subprocess
import webbrowser
import time
import socket
import threading
import shutil
import configparser

# ── Constants ──────────────────────────────────────────────────────
APP_NAME = "VetCoreSoft"
HOSTNAME = "vetcoresoft.local"
PORT = 443
VERSION = "0.3.0"


def get_base_dir():
    """Return the directory where vetcoresoft.exe lives."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_base_dir()
BACKEND_DIR = os.path.join(BASE_DIR, 'backend')
DATA_DIR = os.path.join(BASE_DIR, 'data')
MARKER_FILE = os.path.join(DATA_DIR, '.installed')


# ── Windows helpers ────────────────────────────────────────────────

def is_windows():
    return sys.platform == 'win32'


def is_admin():
    """Check if we have administrator privileges."""
    if not is_windows():
        return os.getuid() == 0
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def elevate_and_rerun():
    """Re-launch this exe with admin privileges (UAC prompt)."""
    if not is_windows():
        print("  [!] Run with sudo for first-time setup.")
        sys.exit(1)

    exe = sys.executable
    params = " ".join(f'"{a}"' for a in sys.argv[1:])
    # ShellExecuteW returns >32 on success
    ret = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", exe, params, None, 1
    )
    if ret <= 32:
        print("  [!] Could not get administrator privileges.")
        print("  The hosts file change is needed only on first run.")
        input("\n  Press Enter to exit...")
        sys.exit(1)
    sys.exit(0)


def is_port_available(port):
    """Check if a TCP port is free on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return True
        except OSError:
            return False


# ── First-run setup ───────────────────────────────────────────────

def setup_hosts():
    """Add vetcoresoft.local → 127.0.0.1 to the Windows hosts file."""
    if not is_windows():
        hosts_path = '/etc/hosts'
    else:
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts"

    try:
        with open(hosts_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(hosts_path, 'r', encoding='latin-1') as f:
            content = f.read()

    if HOSTNAME in content:
        print(f"  [OK] {HOSTNAME} already in hosts file")
        return

    entry = f"\n127.0.0.1    {HOSTNAME}    # VetCoreSoft Desktop\n"
    with open(hosts_path, 'a', encoding='utf-8') as f:
        f.write(entry)
    print(f"  [OK] Added {HOSTNAME} to hosts file")


def create_shortcut():
    """Create a desktop shortcut using PowerShell."""
    if not is_windows():
        print("  [SKIP] Desktop shortcut (not Windows)")
        return

    desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
    shortcut_path = os.path.join(desktop, f'{APP_NAME}.lnk')

    if os.path.exists(shortcut_path):
        print("  [OK] Desktop shortcut already exists")
        return

    exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])
    icon_path = os.path.join(BASE_DIR, 'vetcoresoft.ico')

    # Build PowerShell script to create .lnk
    icon_line = ""
    if os.path.exists(icon_path):
        icon_line = f'\n$Shortcut.IconLocation = "{icon_path}"'

    ps_script = (
        f'$WshShell = New-Object -ComObject WScript.Shell; '
        f'$Shortcut = $WshShell.CreateShortcut("{shortcut_path}"); '
        f'$Shortcut.TargetPath = "{exe_path}"; '
        f'$Shortcut.WorkingDirectory = "{BASE_DIR}"; '
        f'$Shortcut.Description = "VetCoreSoft - Veterinary Management"; '
        f'{icon_line}'
        f'$Shortcut.Save()'
    )

    subprocess.run(
        ['powershell', '-NoProfile', '-Command', ps_script],
        capture_output=True, timeout=10
    )
    print(f"  [OK] Desktop shortcut created")


def generate_ssl_cert():
    """Generate a self-signed certificate for vetcoresoft.local and install it as trusted."""
    cert_dir = os.path.join(DATA_DIR, 'certs')
    os.makedirs(cert_dir, exist_ok=True)

    cert_path = os.path.join(cert_dir, 'vetcoresoft.crt')
    key_path = os.path.join(cert_dir, 'vetcoresoft.key')

    if os.path.exists(cert_path) and os.path.exists(key_path):
        print("  [OK] SSL certificate already exists")
        return cert_path, key_path

    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from datetime import datetime, timedelta, timezone
    import ipaddress

    # Generate private key
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    # Build certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "VetCoreSoft Desktop"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "VetCoreSoft"),
    ])

    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=3650))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("vetcoresoft.local"),
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        )
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        )
        .sign(key, hashes.SHA256())
    )

    # Write key and cert files
    with open(key_path, 'wb') as f:
        f.write(key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        ))

    with open(cert_path, 'wb') as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print("  [OK] SSL certificate generated")

    # Install cert in Windows Trusted Root CA store (requires admin)
    if is_windows() and is_admin():
        try:
            subprocess.run(
                ['certutil', '-addstore', 'Root', cert_path],
                capture_output=True, timeout=10,
            )
            print("  [OK] Certificate installed in Windows trust store")
        except Exception as e:
            print(f"  [!] Could not auto-trust certificate: {e}")
            print(f"      You may need to manually trust: {cert_path}")

    return cert_path, key_path


def get_ssl_paths():
    """Return (cert_path, key_path) for the SSL certificate."""
    cert_dir = os.path.join(DATA_DIR, 'certs')
    return (
        os.path.join(cert_dir, 'vetcoresoft.crt'),
        os.path.join(cert_dir, 'vetcoresoft.key'),
    )


def first_run_setup():
    """First-run: needs admin privileges for hosts file modification."""
    print(f"\n{'=' * 50}")
    print(f"  {APP_NAME} — First Time Setup")
    print(f"{'=' * 50}\n")

    if not is_admin():
        print("  Requesting administrator privileges...")
        print("  (needed to configure the local hostname)\n")
        elevate_and_rerun()
        return  # Won't reach here

    # Create data directory
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, 'media'), exist_ok=True)

    # Configure hosts file
    print("  Configuring hostname...")
    setup_hosts()

    # Generate SSL certificate for HTTPS
    print("  Generating SSL certificate...")
    generate_ssl_cert()

    # Create desktop shortcut
    print("  Creating desktop shortcut...")
    create_shortcut()

    # Write installed marker
    with open(MARKER_FILE, 'w') as f:
        f.write(VERSION)

    print(f"\n  Setup complete!\n")


# ── Django management ─────────────────────────────────────────────

def setup_django_env():
    """Configure the environment so Django can start."""
    # Add backend to Python path
    if BACKEND_DIR not in sys.path:
        sys.path.insert(0, BACKEND_DIR)

    # Core Django env vars
    os.environ['DJANGO_SETTINGS_MODULE'] = 'vetcore.settings'
    os.environ['DEPLOYMENT_MODE'] = 'DESKTOP'
    os.environ['VETCORE_DATA_DIR'] = DATA_DIR
    os.environ['DEBUG'] = '1'

    # Read vetcoresoft.ini for cloud API config
    ini_path = os.path.join(BASE_DIR, 'vetcoresoft.ini')
    if os.path.exists(ini_path):
        config = configparser.ConfigParser()
        config.read(ini_path, encoding='utf-8')
        api_url = config.get('cloud', 'api_url', fallback=None)
        api_secret = config.get('cloud', 'api_secret', fallback=None)
        if api_url:
            os.environ.setdefault('LICENSE_API_URL', api_url.rstrip('/') + '/check-license')
        if api_secret:
            os.environ.setdefault('CLOUD_API_SECRET', api_secret)

    # Change working directory to backend
    os.chdir(BACKEND_DIR)


def run_migrations():
    """Run Django database migrations silently."""
    import django
    django.setup()
    from django.core.management import call_command
    call_command('migrate', '--run-syncdb', verbosity=0)


def start_server():
    """Start Django HTTPS server (--noreload is critical for PyInstaller)."""
    from django.core.management import call_command
    cert_path, key_path = get_ssl_paths()
    if os.path.exists(cert_path) and os.path.exists(key_path):
        call_command(
            'runsslserver', f'0.0.0.0:{PORT}',
            '--noreload',
            '--certificate', cert_path,
            '--key', key_path,
        )
    else:
        # Fallback to plain HTTP if certs not found
        call_command('runserver', f'0.0.0.0:{PORT}', '--noreload')


# ── Main ──────────────────────────────────────────────────────────

def main():
    print(f"\n  VetCoreSoft v{VERSION}")
    print(f"  {'~' * 40}\n")

    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

    # First run → UAC + hosts + shortcut
    if not os.path.exists(MARKER_FILE):
        first_run_setup()

    # Setup Django
    setup_django_env()

    # Check port
    if not is_port_available(PORT):
        print(f"  [!] Port {PORT} is in use by another program.")
        print(f"  Close the other program and try again,")
        print(f"  or check if VetCoreSoft is already running.\n")
        if is_windows():
            input("  Press Enter to exit...")
        sys.exit(1)

    # Run migrations
    print(f"  Updating database...")
    run_migrations()
    print(f"  Database ready.\n")

    # Open browser after short delay
    url = f"https://{HOSTNAME}"

    def _open_browser():
        time.sleep(2)
        webbrowser.open(url)

    threading.Thread(target=_open_browser, daemon=True).start()

    # Start server
    print(f"  Server running at {url}")
    print(f"  Close this window to stop VetCoreSoft.\n")

    try:
        start_server()
    except KeyboardInterrupt:
        print(f"\n  VetCoreSoft stopped.")


if __name__ == '__main__':
    main()
