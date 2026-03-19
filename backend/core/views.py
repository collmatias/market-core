import os
import shutil
import secrets
from django.conf import settings
from django.core.mail import send_mail
from django.http import FileResponse, HttpResponse, HttpResponseNotFound
from django.utils import timezone
from django.utils.translation import gettext as _
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from .decorators import admin_required, localhost_required
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from rest_framework import viewsets

from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from .license import get_hardware_id

from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.forms import SetPasswordForm

from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy

from .models import Client, Patient, Company, UserProfile, EmailVerificationToken
from .serializers import ClientSerializer, PatientSerializer
from .forms import AdminSetPasswordForm, ClientForm, PatientForm, CompanyForm, CompanySettingsForm, SetupForm, RegistrationForm, EmployeeForm, EditEmployeeForm, ChangePinForm
from .utils import get_server_ip
from datetime import date, timedelta
from clinical.models import Appointment
import requests as http_requests
import logging

from django.contrib import messages

from .license import check_license, save_license, generate_offline_key


# --- PUBLIC LANDING PAGE (SaaS download page, no auth required) ---
def landing(request):
    zip_path = os.path.join(settings.BASE_DIR, 'static', 'downloads', 'VetCoreSoft-Setup.zip')
    return render(request, "core/landing.html", {
        'zip_available': os.path.exists(zip_path),
    })


# --- SAAS REGISTRATION (public, SaaS mode only) ---
def register(request):
    """Landing page: choose account type (VET or SUPPLIER)."""
    if getattr(settings, 'DEPLOYMENT_MODE', 'DESKTOP') != 'SAAS':
        return redirect('login')
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'core/register_choose.html')


def register_typed(request, account_type):
    """Registration form for a specific account type."""
    if getattr(settings, 'DEPLOYMENT_MODE', 'DESKTOP') != 'SAAS':
        return redirect('login')
    if request.user.is_authenticated:
        return redirect('home')

    account_type = account_type.upper()
    if account_type not in ('VET', 'SUPPLIER'):
        return redirect('register')

    is_vet = account_type == 'VET'

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try:
                data = form.cleaned_data
                trial_days = 30

                # 1. Register tenant on Cloud API
                tenant_id, tenant_token = _register_tenant_on_cloud(
                    name=data['company_name'],
                    email=data['company_email'],
                    tax_id=data.get('tax_id') or None,
                    phone=data.get('phone') or None,
                    address=data.get('address') or None,
                    region=data.get('region') or None,
                    tenant_type=account_type,
                )

                # 2. Create local Company
                company = Company.objects.create(
                    name=data['company_name'],
                    tax_id=data.get('tax_id') or 'PENDING',
                    address=data.get('address', ''),
                    phone=data.get('phone', ''),
                    email=data['company_email'],
                    is_setup_complete=True,
                    account_type=account_type,
                    plan='TRIAL',
                    expiration_date=date.today() + timedelta(days=trial_days),
                    is_active=True,
                    cloud_tenant_id=tenant_id,
                    cloud_tenant_token=tenant_token or '',
                )

                # 3. Create admin user
                user = User.objects.create_user(
                    username=data['username'],
                    email=data['email'],
                    password=data['password'],
                )
                UserProfile.objects.create(
                    user=user,
                    company=company,
                    role='ADMIN',
                    is_admin=True,
                    is_owner=True,
                )

                # Send verification email (non-blocking)
                _send_verification_email(request, user)

                login(request, user)
                messages.success(request, _('Welcome to VetCoreSoft! Your 30-day trial has started. Please check your email to verify your account.'))
                return redirect('home')
            except Exception as e:
                logger.error(f'Registration error: {e}')
                form.add_error(None, _('An error occurred during registration. Please try again.'))
    else:
        form = RegistrationForm()

    ctx = {
        'form': form,
        'account_type': account_type,
        'is_vet': is_vet,
        'type_icon': '🏥' if is_vet else '📦',
        'type_label': _('Veterinary Clinic') if is_vet else _('Supplier / Distributor'),
        'company_label': _('Clinic Name') if is_vet else _('Company Name'),
        'company_email_label': _('Clinic Email') if is_vet else _('Company Email'),
        'step2_title': _('Your Clinic') if is_vet else _('Your Company'),
        'step2_subtitle': _('Tell us about your clinic') if is_vet else _('Tell us about your company'),
    }
    return render(request, 'core/register.html', ctx)


def _send_verification_email(request, user):
    """Generate token and send verification email. Non-blocking on failure."""
    try:
        token = secrets.token_urlsafe(48)
        EmailVerificationToken.objects.update_or_create(
            user=user,
            defaults={'token': token},
        )
        verify_url = request.build_absolute_uri(f'/verify-email/{token}/')
        send_mail(
            subject=_('VetCoreSoft — Verify your email'),
            message=_('Hi %(username)s,\n\nPlease verify your email by clicking the link below:\n\n%(url)s\n\nThis link expires in 48 hours.\n\n— VetCoreSoft Team') % {
                'username': user.username,
                'url': verify_url,
            },
            from_email=None,
            recipient_list=[user.email],
            fail_silently=True,
        )
    except Exception as e:
        logger.warning('Verification email failed (non-blocking): %s', e)


def verify_email(request, token):
    """Public view — validates email verification token."""
    try:
        vt = EmailVerificationToken.objects.select_related('user__profile').get(token=token)
    except EmailVerificationToken.DoesNotExist:
        messages.error(request, _('Invalid or expired verification link.'))
        return redirect('login')

    # Check if token is older than 48 hours
    age = timezone.now() - vt.created_at
    if age.total_seconds() > 48 * 3600:
        vt.delete()
        messages.error(request, _('This verification link has expired. Please request a new one.'))
        return redirect('login')

    vt.user.profile.email_verified = True
    vt.user.profile.save(update_fields=['email_verified'])
    vt.delete()
    messages.success(request, _('Your email has been verified successfully!'))
    if request.user.is_authenticated:
        return redirect('home')
    return redirect('login')


def resend_verification(request):
    """Resend verification email for the logged-in user."""
    if not request.user.is_authenticated:
        return redirect('login')
    if hasattr(request.user, 'profile') and request.user.profile.email_verified:
        messages.info(request, _('Your email is already verified.'))
        return redirect('home')
    _send_verification_email(request, request.user)
    messages.success(request, _('Verification email sent. Please check your inbox.'))
    return redirect('home')


# --- API VIEWSETS (DRF) ---
class ClientViewSet(viewsets.ModelViewSet):
    serializer_class = ClientSerializer

    def get_queryset(self):
        return Client.objects.filter(
            company=self.request.user.profile.company
        ).order_by("-id")


class PatientViewSet(viewsets.ModelViewSet):
    serializer_class = PatientSerializer

    def get_queryset(self):
        return Patient.objects.filter(
            company=self.request.user.profile.company
        ).order_by("-id")


# --- SECURITY & PROFILE ---
class ChangePasswordView(SuccessMessageMixin, PasswordChangeView):
    template_name = "core/change_password.html"
    success_url = reverse_lazy("home")


@login_required
def reset_employee_password(request, id):
    is_admin = request.user.is_superuser or (hasattr(request.user, "profile") and request.user.profile.role == "ADMIN")
    if not is_admin:
        messages.error(request, _("Access denied. Administrator permissions required."))
        return redirect("home")

    employee = get_object_or_404(User, id=id, profile__company=request.user.profile.company)

    if request.method == "POST":
        form = AdminSetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data["new_password1"]
            employee.set_password(new_password)
            employee.save()
            return redirect("team_management")
    else:
        form = AdminSetPasswordForm()

    return render(request, "core/reset_password.html", {
        "form": form,
        "employee": employee
    })


@login_required
def prepare_quick_switch(request):
    company_id = request.user.profile.company.id
    logout(request)
    response = redirect("lockscreen")
    response.set_cookie("vetcoresoft_workstation", company_id, max_age=43200)
    return response


@ensure_csrf_cookie
def lockscreen(request):
    if request.user.is_authenticated:
        return redirect("home")

    company_id = request.COOKIES.get("vetcoresoft_workstation")
    if not company_id:
        return redirect("login")

    employees = UserProfile.objects.filter(company_id=company_id, user__is_active=True).select_related("user")

    if request.method == "POST":
        user_id = request.POST.get("user_id")
        pin_entered = request.POST.get("pin")

        try:
            profile = UserProfile.objects.get(user__id=user_id, company_id=company_id)
            if profile.pin and profile.pin == pin_entered:
                login(request, profile.user)
                return redirect("home")
            else:
                messages.error(request, _("Incorrect or unconfigured PIN."))
        except UserProfile.DoesNotExist:
            messages.error(request, _("Invalid user."))

    return render(request, "core/lockscreen.html", {"employees": employees})


@login_required
def change_pin(request):
    profile = request.user.profile

    if request.method == "POST":
        form = ChangePinForm(request.POST)
        if form.is_valid():
            profile.pin = form.cleaned_data["new_pin"]
            profile.save()
            return redirect("home")
    else:
        form = ChangePinForm()

    return render(request, "core/change_pin.html", {"form": form})


# --- TEMPLATE VIEWS (FRONTEND) ---

def home(request):
    if not request.user.is_authenticated:
        if getattr(settings, 'DEPLOYMENT_MODE', 'DESKTOP') == 'SAAS':
            return render(request, "core/saas_home.html")
        return redirect('login')
    ip_address = get_server_ip()
    return render(request, "core/home.html", {"server_ip": ip_address})


@admin_required
@login_required
def download_backup(request):
    engine = settings.DATABASES["default"]["ENGINE"]
    if "sqlite3" not in engine:
        return HttpResponse("Backup only available in Local Client Mode (SQLite).", status=501)

    db_path = settings.DATABASES["default"]["NAME"]
    if os.path.exists(db_path):
        date_str = timezone.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"backup_vetcoresoft_{date_str}.sqlite3"
        return FileResponse(open(db_path, "rb"), as_attachment=True, filename=filename)
    else:
        return HttpResponseNotFound("Database file not found.")


# --- CLIENTS ---
@login_required
def client_list(request):
    clients_qs = Client.objects.for_company(request.user)
    q = request.GET.get("q", "").strip()
    if q:
        clients_qs = clients_qs.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(phone__icontains=q) |
            Q(email__icontains=q)
        )
    clients_qs = clients_qs.order_by("last_name", "first_name")
    paginator = Paginator(clients_qs, 25)
    page = request.GET.get("page")
    clients = paginator.get_page(page)
    return render(request, "core/client_list.html", {"clients": clients, "q": q})


@login_required
def create_client(request):
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.company = request.user.profile.company
            client.save()
            messages.success(request, _("Client %(first)s %(last)s registered successfully.") % {"first": client.first_name, "last": client.last_name})
            return redirect("client_list")
    else:
        form = ClientForm()
    return render(request, "core/client_form.html", {"form": form})


@login_required
def edit_client(request, client_id):
    client = get_object_or_404(Client, pk=client_id, company=request.user.profile.company)
    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect("client_list")
    else:
        form = ClientForm(instance=client)
    return render(request, "core/client_form.html", {"form": form, "is_edit": True})


@login_required
def client_detail(request, client_id):
    client = get_object_or_404(Client, pk=client_id, company=request.user.profile.company)
    pets = client.pets.all()
    upcoming_appointments = Appointment.objects.filter(
        patient__owner=client
    ).exclude(status__in=["CANCELLED", "COMPLETED"]).order_by("start_time").select_related("patient", "professional__user")
    past_appointments = Appointment.objects.filter(
        patient__owner=client, status__in=["COMPLETED", "CANCELLED"]
    ).order_by("-start_time").select_related("patient", "professional__user")[:20]

    return render(request, "core/client_detail.html", {
        "client": client,
        "pets": pets,
        "upcoming_appointments": upcoming_appointments,
        "past_appointments": past_appointments,
    })


# --- PATIENTS ---
@login_required
def patient_list(request):
    patients_qs = Patient.objects.for_company(request.user).select_related("owner")
    q = request.GET.get("q", "").strip()
    if q:
        patients_qs = patients_qs.filter(
            Q(name__icontains=q) |
            Q(breed__icontains=q) |
            Q(owner__first_name__icontains=q) |
            Q(owner__last_name__icontains=q)
        )
    patients_qs = patients_qs.order_by("name")
    paginator = Paginator(patients_qs, 25)
    page = request.GET.get("page")
    patients = paginator.get_page(page)
    return render(request, "core/patient_list.html", {"patients": patients, "q": q})


@login_required
def create_patient(request):
    if request.method == "POST":
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.company = request.user.profile.company
            patient.save()
            messages.success(request, _("Patient %(name)s registered successfully.") % {"name": patient.name})
            return redirect("patient_list")
    else:
        form = PatientForm()
    return render(request, "core/patient_form.html", {"form": form})


@login_required
def edit_patient(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    if request.method == "POST":
        form = PatientForm(request.POST, request.FILES, instance=patient)
        if form.is_valid():
            form.save()
            return redirect("patient_list")
    else:
        form = PatientForm(instance=patient)
    return render(request, "core/patient_form.html", {"form": form, "is_edit": True})


@login_required
def patient_detail(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    history = patient.medical_history.all().order_by("-date")[:10]
    upcoming_appointments = patient.appointments.exclude(
        status__in=["CANCELLED", "COMPLETED"]
    ).order_by("start_time").select_related("professional__user")
    past_appointments = patient.appointments.filter(
        status__in=["COMPLETED", "CANCELLED"]
    ).order_by("-start_time").select_related("professional__user")[:20]

    return render(request, "core/patient_detail.html", {
        "patient": patient,
        "history": history,
        "upcoming_appointments": upcoming_appointments,
        "past_appointments": past_appointments,
    })


# --- ACTIVATION & LICENSE ---

def activation(request):
    is_valid, hw_id = check_license()
    if is_valid:
        return redirect("home")

    error = None
    if request.method == "POST":
        key_entered = request.POST.get("serial_key", "").strip().upper()

        if key_entered.startswith("SUB-"):
            save_license(key_entered)
            return redirect("home")

        key_clean = key_entered.replace("-", "")
        key_expected = generate_offline_key(hw_id)

        if key_clean == key_expected:
            save_license(key_expected)
            return redirect("home")
        else:
            error = _("Invalid key. Please verify your code or internet connection.")

    return render(request, "core/activation.html", {
        "hardware_id": hw_id,
        "error": error
    })


@login_required
@admin_required
def company_settings(request):
    try:
        company = request.user.profile.company
        is_new = False
    except (Company.DoesNotExist, UserProfile.DoesNotExist, AttributeError):
        company = Company.objects.first()
        is_new = True if not company else False

    if request.method == "POST":
        form = CompanySettingsForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            return redirect("home")
    else:
        form = CompanySettingsForm(instance=company)

    return render(request, "core/company_settings.html", {
        "form": form,
        "company": company,
        "is_new": is_new
    })


def setup_wizard(request):
    if User.objects.filter(is_superuser=True).exists():
        return redirect("home")

    if request.method == "POST":
        form = SetupForm(request.POST)
        if form.is_valid():
            try:
                data = form.cleaned_data
                hw_id = get_hardware_id()
                trial_days = 30
                company = Company.objects.create(
                    name=data["company_name"],
                    tax_id=data["tax_id"],
                    address=data["address"],
                    phone=data["phone"],
                    email=data["company_email"],
                    hardware_id=hw_id,
                    is_setup_complete=True,
                    plan="TRIAL",
                    expiration_date=date.today() + timedelta(days=trial_days),
                    is_active=True
                )
                user = User.objects.create_superuser(
                    username=data["username"],
                    email=data["email"],
                    password=data["password"]
                )
                UserProfile.objects.create(
                    user=user,
                    company=company,
                    role="ADMIN",
                    is_admin=True,
                    is_owner=True
                )

                # Register trial license with Cloud API
                _register_trial_on_cloud(
                    hw_id=hw_id,
                    client_name=data["company_name"],
                    client_email=data["company_email"],
                    company_name=data["company_name"],
                    company_email=data["company_email"],
                    company_tax_id=data["tax_id"],
                    trial_days=trial_days,
                )

                login(request, user)
                return redirect("home")
            except Exception as e:
                form.add_error(None, f"Internal error: {str(e)}")
    else:
        form = SetupForm()

    return render(request, "core/setup_wizard.html", {"form": form})


logger = logging.getLogger(__name__)


def _register_trial_on_cloud(hw_id, client_name, client_email, company_name,
                              company_email, company_tax_id, trial_days=30):
    """Register a TRIAL license on the Cloud API. Fire-and-forget — failure doesn't block setup."""
    from .license import AWS_LAMBDA_URL, get_cloud_api_secret
    # Derive the cloud API base from the license URL
    base_url = AWS_LAMBDA_URL.rsplit('/', 1)[0]  # e.g. http://cloud_api:8000
    try:
        # First get a JWT token
        token_resp = http_requests.post(
            f"{base_url}/admin/login",
            json={"secret": get_cloud_api_secret()},
            timeout=5
        )
        if token_resp.status_code != 200:
            logger.warning("Could not get cloud API token for trial registration")
            return
        token = token_resp.json().get("access_token")

        # Create the trial license
        http_requests.post(
            f"{base_url}/license/admin/create",
            json={
                "hw_id": hw_id,
                "client_name": client_name,
                "client_email": client_email,
                "company_name": company_name,
                "company_email": company_email,
                "company_tax_id": company_tax_id,
                "plan": "TRIAL",
                "expiration_date": (date.today() + timedelta(days=trial_days)).isoformat(),
            },
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
    except Exception as e:
        logger.warning("Trial cloud registration failed (non-blocking): %s", e)


def _register_tenant_on_cloud(name, email, tax_id=None, phone=None, address=None, region=None, tenant_type='VET'):
    """Register a Tenant on the Cloud API. Returns (tenant_id, token) or (None, None)."""
    from .license import AWS_LAMBDA_URL
    base_url = AWS_LAMBDA_URL.rsplit('/', 1)[0]
    try:
        resp = http_requests.post(
            f"{base_url}/tenant/register",
            json={
                "name": name,
                "email": email,
                "tax_id": tax_id,
                "phone": phone,
                "address": address,
                "region": region,
                "type": tenant_type,
            },
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("id"), data.get("token")
        logger.warning("Tenant registration returned %s: %s", resp.status_code, resp.text)
    except Exception as e:
        logger.warning("Tenant cloud registration failed (non-blocking): %s", e)
    return None, None


@login_required
def team_management(request):
    is_admin_profile = hasattr(request.user, "profile") and request.user.profile.role == "ADMIN"
    if not (request.user.is_superuser or is_admin_profile):
        messages.error(request, _("Access denied. Administrator permissions required."))
        return redirect("home")

    current_company = request.user.profile.company

    if request.method == "POST":
        form = EmployeeForm(request.POST)
        if form.is_valid():
            try:
                data = form.cleaned_data
                new_user = User.objects.create_user(
                    username=data["username"],
                    email=data["email"],
                    password=data["password"],
                    first_name=data["first_name"],
                    last_name=data["last_name"]
                )
                UserProfile.objects.create(
                    user=new_user,
                    company=current_company,
                    role=data["role"],
                    is_admin=data.get("is_admin", False),
                    license_number=data["license_number"],
                    pin=data.get("pin"),
                    avatar=data.get("avatar", "bi-person-fill")
                )
                messages.success(request, _("Employee %(name)s created successfully.") % {"name": new_user.username})
                return redirect("team_management")
            except Exception as e:
                messages.error(request, _("Error creating user: %(error)s") % {"error": e})
    else:
        form = EmployeeForm()

    employees = UserProfile.objects.filter(company=current_company).select_related("user")
    return render(request, "core/team_management.html", {
        "employees": employees,
        "form": form
    })


@login_required
def edit_employee(request, id):
    is_admin = request.user.is_superuser or (hasattr(request.user, "profile") and request.user.profile.role == "ADMIN")
    if not is_admin:
        messages.error(request, _("Access denied."))
        return redirect("home")

    employee = get_object_or_404(User, id=id, profile__company=request.user.profile.company)
    profile = employee.profile

    if request.method == "POST":
        form = EditEmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            profile.role = form.cleaned_data["role"]
            profile.is_admin = form.cleaned_data.get("is_admin", False)
            profile.license_number = form.cleaned_data["license_number"]
            profile.avatar = form.cleaned_data["avatar"]
            new_pin = form.cleaned_data.get("pin")
            if new_pin:
                profile.pin = new_pin
            profile.save()
            messages.success(request, _("%(name)s data updated.") % {"name": employee.first_name})
            return redirect("team_management")
    else:
        form = EditEmployeeForm(instance=employee, initial={
            "role": profile.role,
            "is_admin": profile.is_admin,
            "license_number": profile.license_number,
            "avatar": profile.avatar
        })

    return render(request, "core/edit_employee.html", {"form": form, "employee": employee})


@login_required
def toggle_employee_status(request, id):
    if request.method != "POST":
        return redirect("team_management")
    is_admin = request.user.is_superuser or (hasattr(request.user, "profile") and request.user.profile.role == "ADMIN")
    if not is_admin:
        return redirect("home")

    employee = get_object_or_404(User, id=id, profile__company=request.user.profile.company)
    if employee == request.user:
        messages.error(request, _("You cannot deactivate your own admin account."))
        return redirect("team_management")

    employee.is_active = not employee.is_active
    employee.save()

    status = _("activated") if employee.is_active else _("deactivated")
    msg_func = messages.success if employee.is_active else messages.warning
    msg_func(request, _("User %(name)s has been %(status)s.") % {"name": employee.username, "status": status})
    return redirect("team_management")


# --- IMPORT HUB ---
@login_required
@admin_required
@localhost_required
def import_hub(request):
    return render(request, "core/import_hub.html")


# --- VETTER IMPORT ---
@login_required
@admin_required
@localhost_required
def vetter_import(request):
    result = None
    log = None
    error = None
    data_dir = ''

    if request.method == "POST":
        data_dir = request.POST.get("data_dir", "").strip()

        if not os.path.isabs(data_dir):
            error = _("Please provide an absolute path (starting with /).")
        else:
            from core.services.vetter_import import VetterImporter

            importer = VetterImporter(data_dir, request.user.profile.company)
            valid, msg = importer.validate()
            if not valid:
                error = msg
            else:
                try:
                    # Auto-backup before import
                    db_path = settings.DATABASES["default"]["NAME"]
                    if "sqlite3" in settings.DATABASES["default"]["ENGINE"] and os.path.exists(db_path):
                        date_str = timezone.now().strftime("%Y%m%d_%H%M%S")
                        safety_path = f"{db_path}.pre_import_{date_str}"
                        shutil.copy2(db_path, safety_path)

                    selected_tables = request.POST.getlist("tables")
                    result, log = importer.run(tables=selected_tables if selected_tables else None)
                except Exception as e:
                    error = str(e)

    return render(request, "core/vetter_import.html", {
        "result": result,
        "log": log,
        "error": error,
        "data_dir": data_dir,
    })


@login_required
@admin_required
@localhost_required
def vetter_analyze(request):
    """Return record counts per Vetter table as JSON."""
    from django.http import JsonResponse
    from core.services.vetter_import import VetterImporter

    data_dir = request.GET.get("path", "").strip()
    if not data_dir or not os.path.isabs(data_dir):
        return JsonResponse({"error": "Invalid path"}, status=400)

    importer = VetterImporter(data_dir, request.user.profile.company)
    valid, msg = importer.validate()
    if not valid:
        return JsonResponse({"error": msg}, status=400)

    counts = importer.analyze()
    return JsonResponse({"counts": counts})


@login_required
@admin_required
@localhost_required
def browse_server_dirs(request):
    """AJAX endpoint: returns subdirectories of a given path on the server."""
    parent = request.GET.get("path", "/").strip()
    parent = os.path.realpath(parent)

    if not os.path.isabs(parent) or not os.path.isdir(parent):
        return JsonResponse({"error": "Invalid directory"}, status=400)

    dirs = []
    has_dbf = False
    try:
        for entry in sorted(os.scandir(parent), key=lambda e: e.name.lower()):
            if entry.is_dir(follow_symlinks=False) and not entry.name.startswith('.'):
                dirs.append(entry.name)
            elif entry.name.upper().endswith('.DBF'):
                has_dbf = True
    except PermissionError:
        return JsonResponse({"error": "Permission denied"}, status=403)

    return JsonResponse({
        "path": parent,
        "parent": os.path.dirname(parent) if parent != "/" else None,
        "dirs": dirs,
        "has_dbf": has_dbf,
    })


# --- RESTORE BACKUP ---
@login_required
@admin_required
@localhost_required
def restore_backup(request):
    engine = settings.DATABASES["default"]["ENGINE"]
    if "sqlite3" not in engine:
        messages.error(request, _("Restore only available in Local Client Mode (SQLite)."))
        return redirect("home")

    done = False
    if request.method == "POST" and request.FILES.get("backup_file"):
        backup_file = request.FILES["backup_file"]

        if not backup_file.name.endswith(".sqlite3"):
            messages.error(request, _("Invalid file. Please upload a .sqlite3 backup file."))
            return redirect("restore_backup")

        if backup_file.size > 500 * 1024 * 1024:
            messages.error(request, _("File too large (max 500 MB)."))
            return redirect("restore_backup")

        # Validate it's a real SQLite file (magic bytes)
        header = backup_file.read(16)
        backup_file.seek(0)
        if not header.startswith(b"SQLite format 3"):
            messages.error(request, _("The file is not a valid SQLite database."))
            return redirect("restore_backup")

        db_path = settings.DATABASES["default"]["NAME"]

        # Create a safety backup before overwriting
        date_str = timezone.now().strftime("%Y%m%d_%H%M%S")
        safety_path = f"{db_path}.pre_restore_{date_str}"
        if os.path.exists(db_path):
            shutil.copy2(db_path, safety_path)

        # Close all DB connections before replacing
        from django.db import connections
        for conn in connections.all():
            conn.close()

        # Write uploaded file to the database path
        with open(db_path, "wb") as f:
            for chunk in backup_file.chunks():
                f.write(chunk)

        done = True

    return render(request, "core/restore_backup.html", {"done": done})
