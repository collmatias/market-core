import os
from django.conf import settings
from django.http import FileResponse, HttpResponse, HttpResponseNotFound
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .decorators import admin_requerido
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework import viewsets

from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from .license import get_hardware_id

from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.forms import SetPasswordForm

from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy

from .models import Cliente, Paciente, Empresa, UserProfile
from .serializers import ClienteSerializer, PacienteSerializer
from .forms import AdminSetPasswordForm, ClienteForm, PacienteForm, EmpresaForm, SetupForm, EmpleadoForm, EditarEmpleadoForm, CambiarPinForm
from .utils import get_server_ip
from datetime import date, timedelta

from django.contrib import messages

# --- CORRECCIÓN AQUÍ: Importamos 'generate_offline_key' ---
from .license import check_license, save_license, generate_offline_key

# --- API VIEWSETS (DRF) ---
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all().order_by('-id')
    serializer_class = ClienteSerializer

class PacienteViewSet(viewsets.ModelViewSet):
    queryset = Paciente.objects.all().order_by('-id')
    serializer_class = PacienteSerializer

# --- SEGURIDAD Y PERFIL ---
class CambiarPasswordView(SuccessMessageMixin, PasswordChangeView):
    template_name = 'core/cambiar_password.html'
    success_url = reverse_lazy('home')
    success_message = "¡Tu contraseña ha sido actualizada con éxito!"

@login_required
def resetear_password_empleado(request, id):
    # Seguridad: Solo el ADMIN puede hacer esto
    es_admin = request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.rol == 'ADMIN')
    if not es_admin:
        messages.error(request, "Acceso denegado. Se requieren permisos de Administrador.")
        return redirect('home')

    # Buscamos al empleado asegurando que sea de la misma empresa
    empleado = get_object_or_404(User, id=id, profile__empresa=request.user.profile.empresa)

    if request.method == 'POST':
        # Usamos nuestro formulario sin reglas
        form = AdminSetPasswordForm(request.POST)
        if form.is_valid():
            nueva_clave = form.cleaned_data['new_password1']
            
            # GUARDADO MANUAL FORZADO (se salta las validaciones de settings.py)
            empleado.set_password(nueva_clave)
            empleado.save()
            
            messages.success(request, f"¡Contraseña actualizada con éxito para {empleado.first_name}!")
            return redirect('gestion_equipo')
    else:
        form = AdminSetPasswordForm()

    return render(request, 'core/resetear_password.html', {
        'form': form, 
        'empleado': empleado
    })

@login_required
def preparar_cambio_rapido(request):
    """Cierra la sesión actual pero deja la PC lista para cambiar rápidamente a otro usuario de la misma veterinaria usando solo un PIN."""
    empresa_id = request.user.profile.empresa.id
    logout(request) # Cerramos sesión por seguridad
    
    # Redirigimos a la pantalla de PIN
    response = redirect('lockscreen')
    # Guardamos en una cookie de 12 horas de qué veterinaria es esta PC
    response.set_cookie('vetcore_workstation', empresa_id, max_age=43200) 
    return response

def lockscreen(request):
    """La pantalla gráfica estilo iPad para elegir usuario"""
    # Si ya hay alguien logueado, lo mandamos al home
    if request.user.is_authenticated:
        return redirect('home')

    # Leemos la cookie para saber qué empleados mostrar
    empresa_id = request.COOKIES.get('vetcore_workstation')
    
    if not empresa_id:
        # Si no hay cookie (borraron el historial), a login normal
        return redirect('login')
        
    # Traemos a todos los empleados activos de esa veterinaria
    empleados = UserProfile.objects.filter(empresa_id=empresa_id, user__is_active=True).select_related('user')

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        pin_ingresado = request.POST.get('pin')
        
        try:
            perfil = UserProfile.objects.get(user__id=user_id, empresa_id=empresa_id)
            if perfil.pin and perfil.pin == pin_ingresado:
                # ¡PIN CORRECTO! Logueamos al usuario instantáneamente
                login(request, perfil.user)
                return redirect('home')
            else:
                messages.error(request, "PIN incorrecto o no configurado.")
        except UserProfile.DoesNotExist:
            messages.error(request, "Usuario inválido.")

    return render(request, 'core/lockscreen.html', {'empleados': empleados})

@login_required
def cambiar_pin(request):
    perfil = request.user.profile

    if request.method == 'POST':
        form = CambiarPinForm(request.POST)
        if form.is_valid():
            # Guardamos el nuevo PIN en el perfil del usuario logueado
            perfil.pin = form.cleaned_data['nuevo_pin']
            perfil.save()
            
            messages.success(request, "¡Tu PIN de acceso rápido ha sido actualizado con éxito!")
            return redirect('home')
    else:
        form = CambiarPinForm()

    return render(request, 'core/cambiar_pin.html', {'form': form})

# --- VISTAS TEMPLATES (FRONTEND) ---

@login_required
def home(request):
    ip_address = get_server_ip()
    return render(request, 'core/home.html', {'server_ip': ip_address})

@admin_requerido
@login_required
def descargar_backup(request):
    engine = settings.DATABASES['default']['ENGINE']
    if 'sqlite3' not in engine:
        return HttpResponse(
            "El backup directo solo está disponible en Modo Cliente Local (SQLite).", 
            status=501
        )

    db_path = settings.DATABASES['default']['NAME']
    
    if os.path.exists(db_path):
        fecha = timezone.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"backup_vetcore_{fecha}.sqlite3"
        return FileResponse(open(db_path, 'rb'), as_attachment=True, filename=filename)
    else:
        return HttpResponseNotFound("El archivo de base de datos no se encuentra.")

# --- CLIENTES ---
@login_required
def lista_clientes(request):
    clientes = Cliente.objects.all().order_by('-id')
    return render(request, 'core/lista_clientes.html', {'clientes': clientes})

@login_required
def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            # 1. Pausamos el guardado
            cliente = form.save(commit=False)
            # 2. Inyectamos la empresa
            cliente.empresa = request.user.profile.empresa
            # 3. Guardamos definitivamente
            cliente.save()
            
            messages.success(request, f"Cliente {cliente.nombre} {cliente.apellido} registrado con éxito.")
            return redirect('lista_clientes')
    else:
        form = ClienteForm()
    return render(request, 'core/cliente_form.html', {'form': form})

@login_required
def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('lista_clientes')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'core/cliente_form.html', {'form': form, 'es_edicion': True})

# --- PACIENTES ---
@login_required
def lista_pacientes(request):
    pacientes = Paciente.objects.para_empresa(request.user)
    return render(request, 'core/lista_pacientes.html', {'pacientes': pacientes})

@login_required
def crear_paciente(request):
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            # 1. Pausamos el guardado
            paciente = form.save(commit=False)
            # 2. Inyectamos la empresa
            paciente.empresa = request.user.profile.empresa
            # 3. Guardamos definitivamente
            paciente.save()
            
            messages.success(request, f"Paciente {paciente.nombre} registrado con éxito.")
            return redirect('lista_pacientes')
    else:
        form = PacienteForm()
    return render(request, 'core/paciente_form.html', {'form': form})

@login_required
def editar_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    if request.method == 'POST':
        form = PacienteForm(request.POST, request.FILES, instance=paciente)
        if form.is_valid():
            form.save()
            return redirect('lista_pacientes')
    else:
        form = PacienteForm(instance=paciente)
    return render(request, 'core/paciente_form.html', {'form': form, 'es_edicion': True})

# --- SISTEMA DE ACTIVACIÓN Y LICENCIAS ---

def activacion(request):
    # 1. Verificamos si ya tiene licencia válida (Online u Offline)
    is_valid, hw_id = check_license()
    
    if is_valid:
        return redirect('home')
        
    error = None
    if request.method == 'POST':
        key_ingresada = request.POST.get('serial_key', '').strip().upper()
        
        # CASO A: Clave Online (Empieza con SUB-)
        # No validamos matemáticamente, solo guardamos y dejamos que el middleware chequee contra la API
        if key_ingresada.startswith("SUB-"):
            save_license(key_ingresada)
            return redirect('home') # El middleware hará la validación real contra tu Docker Cloud API

        # CASO B: Clave Perpetua (Offline)
        # 1. Quitamos guiones para comparar la matemática pura
        key_limpia = key_ingresada.replace('-', '') 

        # 2. Generamos la clave esperada OFFLINE
        key_esperada = generate_offline_key(hw_id)
        
        # 3. Comparamos
        if key_limpia == key_esperada:
            save_license(key_esperada) # Guardamos la limpia
            return redirect('home')
        else:
            error = "Clave incorrecta. Verifique el código o su conexión a internet."
    
    return render(request, 'core/activacion.html', {
        'hardware_id': hw_id,
        'error': error
    })

@login_required
def configuracion_empresa(request):
    try:
        # CAMBIO 1: Ahora usamos .profile por el related_name que definimos
        empresa = request.user.profile.empresa
        es_nuevo = False
    except:
        # Si falla, buscamos la primera empresa o asumimos que es nuevo
        empresa = Empresa.objects.first()
        es_nuevo = True if not empresa else False

    if request.method == 'POST':
        form = EmpresaForm(request.POST, instance=empresa)
        if form.is_valid():
            nueva_empresa = form.save(commit=False)
            
            # Asignar fecha de vencimiento si no tiene
            if not nueva_empresa.fecha_vencimiento:
                nueva_empresa.fecha_vencimiento = date.today() + timedelta(days=365)
                
            nueva_empresa.save()
            
            # CAMBIO 2: Magia pura. get_or_create evita el error UNIQUE.
            # Si el perfil no existe, lo crea con rol ADMIN. Si existe, no hace nada.
            UserProfile.objects.get_or_create(
                user=request.user,
                defaults={
                    'empresa': nueva_empresa,
                    'rol': 'ADMIN'
                }
            )
            
            return redirect('home')
    else:
        form = EmpresaForm(instance=empresa)

    return render(request, 'core/configuracion_empresa.html', {
        'form': form,
        'es_nuevo': es_nuevo
    })

def setup_wizard(request):
    if User.objects.filter(is_superuser=True).exists():
        return redirect('home')

    if request.method == 'POST':
        form = SetupForm(request.POST)
        if form.is_valid():
            try:
                data = form.cleaned_data
                
                # Crear Empresa
                empresa = Empresa.objects.create(
                    nombre=data['nombre_empresa'],
                    cuit=data['cuit'],
                    direccion=data['direccion'],
                    telefono=data['telefono'],
                    plan='TRIAL',
                    fecha_vencimiento=date.today() + timedelta(days=30),
                    activo=True
                )
                
                # Crear Usuario
                user = User.objects.create_superuser(
                    username=data['username'],
                    email=data['email'],
                    password=data['password']
                )
                
                UserProfile.objects.create(user=user, empresa=empresa)
                login(request, user)
                return redirect('home')

            except Exception as e:
                # Si algo explota (ej: CUIT duplicado o Usuario existente), lo mostramos
                form.add_error(None, f"Error interno: {str(e)}")
                print(f"❌ ERROR AL GUARDAR: {e}") # <--- MIRA LA TERMINAL

        else:
            # Si el formulario es inválido, imprimimos POR QUÉ
            print("❌ EL FORMULARIO NO ES VÁLIDO:") # <--- MIRA LA TERMINAL
            print(form.errors)                      # <--- MIRA LA TERMINAL
    else:
        form = SetupForm()

    return render(request, 'core/setup_wizard.html', {'form': form})

@login_required
def gestion_equipo(request):
    # 1. SEGURIDAD MEJORADA: Pasa si es ADMIN en su perfil, o si es un superusuario de la terminal
    es_admin_perfil = hasattr(request.user, 'profile') and request.user.profile.rol == 'ADMIN'
    
    if not (request.user.is_superuser or es_admin_perfil):
        messages.error(request, "Acceso denegado. Se requieren permisos de Administrador.")
        return redirect('home')

    empresa_actual = request.user.profile.empresa

    if request.method == 'POST':
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            try:
                data = form.cleaned_data
                
                # 2. Crear el Usuario de Django
                nuevo_user = User.objects.create_user(
                    username=data['username'],
                    email=data['email'],
                    password=data['password'],
                    first_name=data['first_name'],
                    last_name=data['last_name']
                )

                # 3. Crear su Perfil (Vinculado a la MISMA empresa)
                UserProfile.objects.create(
                    user=nuevo_user,
                    empresa=empresa_actual,
                    rol=data['rol'],
                    matricula=data['matricula'],
                    pin=data.get('pin'),
                    avatar=data.get('avatar', 'bi-person-fill')
                )

                messages.success(request, f"Empleado {nuevo_user.username} creado con éxito.")
                return redirect('gestion_equipo')
                
            except Exception as e:
                messages.error(request, f"Error al crear usuario: {e}")
    else:
        form = EmpleadoForm()

    # Listar solo empleados de MI empresa
    empleados = UserProfile.objects.filter(empresa=empresa_actual).select_related('user')

    return render(request, 'core/gestion_equipo.html', {
        'empleados': empleados,
        'form': form
    })

@login_required
def editar_empleado(request, id):
    # Seguridad: Solo admin
    es_admin = request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.rol == 'ADMIN')
    if not es_admin:
        messages.error(request, "Acceso denegado.")
        return redirect('home')

    # Buscamos al usuario asegurándonos de que pertenezca a la misma veterinaria
    empleado = get_object_or_404(User, id=id, profile__empresa=request.user.profile.empresa)
    perfil = empleado.profile

    if request.method == 'POST':
        form = EditarEmpleadoForm(request.POST, instance=empleado)
        if form.is_valid():
            form.save() 
            perfil.rol = form.cleaned_data['rol']
            perfil.matricula = form.cleaned_data['matricula']
            perfil.avatar = form.cleaned_data['avatar']
            
            # Solo actualizar el PIN si escribieron algo nuevo
            nuevo_pin = form.cleaned_data.get('pin')
            if nuevo_pin:
                perfil.pin = nuevo_pin
                
            perfil.save()
            
            messages.success(request, f"Datos de {empleado.first_name} actualizados.")
            return redirect('gestion_equipo')
    else:
        # Pre-cargar los datos del perfil en el formulario
        form = EditarEmpleadoForm(instance=empleado, initial={
            'rol': perfil.rol,
            'matricula': perfil.matricula,
            # No enviamos el PIN inicial por seguridad, que se vea en blanco siempre
            'avatar': perfil.avatar
        })

    return render(request, 'core/editar_empleado.html', {'form': form, 'empleado': empleado})

@login_required
def estado_empleado(request, id):
    # Vista interruptor: Activa/Desactiva al usuario
    es_admin = request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.rol == 'ADMIN')
    if not es_admin:
        return redirect('home')

    empleado = get_object_or_404(User, id=id, profile__empresa=request.user.profile.empresa)
    
    # Evitar que el admin se desactive a sí mismo por accidente
    if empleado == request.user:
        messages.error(request, "No puedes desactivar tu propia cuenta de administrador.")
        return redirect('gestion_equipo')

    # Invertir el estado
    empleado.is_active = not empleado.is_active
    empleado.save()
    
    estado = "activado" if empleado.is_active else "desactivado (sin acceso)"
    tipo_mensaje = messages.success if empleado.is_active else messages.warning
    tipo_mensaje(request, f"El usuario {empleado.username} ha sido {estado}.")
    
    return redirect('gestion_equipo')