"""
Management command: rundesktop
Starts MarketCoreSoft in desktop mode with HTTPS (required for camera access).
Generates a self-signed certificate on first run and opens the browser.

Usage: python manage.py rundesktop
       python manage.py rundesktop --port 8443 --no-browser
"""
import os
import ssl
import socket
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application


CERT_DIR_NAME = 'certs'


class Command(BaseCommand):
    help = 'Start MarketCoreSoft desktop server with HTTPS for camera support'

    def add_arguments(self, parser):
        parser.add_argument('--host', default='0.0.0.0', help='Bind address (default: 0.0.0.0)')
        parser.add_argument('--port', type=int, default=443, help='HTTPS port (default: 443)')
        parser.add_argument('--no-browser', action='store_true', help='Do not open browser automatically')

    def handle(self, *args, **options):
        host = options['host']
        port = options['port']
        open_browser = not options['no_browser']

        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        cert_dir = base_dir / CERT_DIR_NAME
        cert_file = cert_dir / 'server.crt'
        key_file = cert_dir / 'server.key'

        # Generate certificate if missing
        if not cert_file.exists() or not key_file.exists():
            self._generate_cert(cert_dir, cert_file, key_file)

        # Run migrations silently
        self.stdout.write('📦 Checking database...')
        call_command('migrate', '--run-syncdb', verbosity=0)

        # Compile translations
        try:
            call_command('compilemessages', verbosity=0)
        except Exception:
            pass  # gettext may not be installed on Windows

        local_ip = self._get_local_ip()
        url = f'https://localhost:{port}' if port != 443 else 'https://localhost'

        self.stdout.write(self.style.SUCCESS(f'\n🏪 MarketCoreSoft Desktop'))
        self.stdout.write(self.style.SUCCESS('─' * 50))
        self.stdout.write(f'   🔒 Local:   {url}')
        if local_ip:
            lan_url = f'https://{local_ip}:{port}' if port != 443 else f'https://{local_ip}'
            self.stdout.write(f'   📱 Network: {lan_url}')
        self.stdout.write(self.style.SUCCESS('─' * 50))
        self.stdout.write('   Press Ctrl+C to stop.\n')

        if open_browser:
            threading.Timer(1.5, lambda: webbrowser.open(url)).start()

        self._run_https_server(host, port, str(cert_file), str(key_file))

    def _generate_cert(self, cert_dir, cert_file, key_file):
        """Generate a self-signed certificate for HTTPS."""
        cert_dir.mkdir(parents=True, exist_ok=True)

        self.stdout.write('🔐 Generating SSL certificate...')

        local_ip = self._get_local_ip()
        san_entries = ['DNS:localhost', 'IP:127.0.0.1', 'IP:::1']
        if local_ip:
            san_entries.append(f'IP:{local_ip}')
        san = ','.join(san_entries)

        # Try openssl (available on most systems)
        try:
            subprocess.run([
                'openssl', 'req', '-x509', '-newkey', 'rsa:2048',
                '-keyout', str(key_file), '-out', str(cert_file),
                '-days', '3650', '-nodes',
                '-subj', '/CN=MarketCoreSoft/O=MarketCoreSoft/C=AR',
                '-addext', f'subjectAltName={san}',
            ], check=True, capture_output=True)
            self.stdout.write(self.style.SUCCESS('   ✅ Certificate generated with openssl.'))
            return
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

        # Fallback: use Python's cryptography library if available
        try:
            self._generate_cert_python(cert_file, key_file, local_ip)
            self.stdout.write(self.style.SUCCESS('   ✅ Certificate generated.'))
            return
        except ImportError:
            pass

        self.stderr.write(self.style.ERROR(
            '❌ Cannot generate SSL certificate.\n'
            '   Install OpenSSL or run: pip install cryptography'
        ))
        sys.exit(1)

    def _generate_cert_python(self, cert_file, key_file, local_ip):
        """Generate certificate using the cryptography library."""
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import datetime
        import ipaddress

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        san_names = [
            x509.DNSName('localhost'),
            x509.IPAddress(ipaddress.ip_address('127.0.0.1')),
            x509.IPAddress(ipaddress.ip_address('::1')),
        ]
        if local_ip:
            san_names.append(x509.IPAddress(ipaddress.ip_address(local_ip)))

        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, 'MarketCoreSoft'),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'MarketCoreSoft'),
            x509.NameAttribute(NameOID.COUNTRY_NAME, 'AR'),
        ])

        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
            .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650))
            .add_extension(x509.SubjectAlternativeName(san_names), critical=False)
            .sign(private_key, hashes.SHA256())
        )

        with open(key_file, 'wb') as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            ))

        with open(cert_file, 'wb') as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

    def _get_local_ip(self):
        """Get the machine's LAN IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return None

    def _run_https_server(self, host, port, certfile, keyfile):
        """Run a threaded HTTPS WSGI server."""
        from wsgiref.simple_server import make_server, WSGIRequestHandler
        import socketserver

        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketcore.settings')
        application = get_wsgi_application()

        class QuietHandler(WSGIRequestHandler):
            def log_message(self, format, *args):
                # Only log errors, not every request
                if args and str(args[0]).startswith(('4', '5')):
                    super().log_message(format, *args)

        class ThreadedWSGIServer(socketserver.ThreadingMixIn, type(make_server('', 0, None).__class__)):
            daemon_threads = True
            allow_reuse_address = True

        # Build the server manually to use our threaded class
        from wsgiref.simple_server import WSGIServer
        class ThreadedSSLServer(socketserver.ThreadingMixIn, WSGIServer):
            daemon_threads = True
            allow_reuse_address = True

        server = ThreadedSSLServer((host, port), QuietHandler)
        server.set_app(application)

        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(certfile=certfile, keyfile=keyfile)
        server.socket = ctx.wrap_socket(server.socket, server_side=True)

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            self.stdout.write('\n👋 Server stopped.')
            server.shutdown()
