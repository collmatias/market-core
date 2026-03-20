import os
import shutil
from django.conf import settings
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

from .models import Client, Company, UserProfile
from .serializers import ClientSerializer
from .forms import AdminSetPasswordForm, ClientForm, CompanyForm, SetupForm, EmployeeForm, EditEmployeeForm, ChangePinForm
from .utils import get_server_ip
from datetime import date, timedelta

from django.contrib import messages

from .license import check_license, save_license, generate_offline_key


# --- API VIEWSETS (DRF) ---
class ClientViewSet(viewsets.ModelViewSet):
    serializer_class = ClientSerializer

    def get_queryset(self):
        return Client.objects.filter(
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
    response.set_cookie("marketcore_workstation", company_id, max_age=43200)
    return response


@ensure_csrf_cookie
def lockscreen(request):
    if request.user.is_authenticated:
        return redirect("home")

    company_id = request.COOKIES.get("marketcore_workstation")
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

@login_required
def home(request):
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
        filename = f"backup_marketcore_{date_str}.sqlite3"
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
    purchases = client.purchases.all().order_by('-date')[:20]

    return render(request, "core/client_detail.html", {
        "client": client,
        "purchases": purchases,
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
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            new_company = form.save(commit=False)
            if not new_company.expiration_date:
                new_company.expiration_date = date.today() + timedelta(days=365)
            new_company.save()

            UserProfile.objects.get_or_create(
                user=request.user,
                defaults={
                    "company": new_company,
                    "role": "ADMIN"
                }
            )
            return redirect("home")
    else:
        form = CompanyForm(instance=company)

    return render(request, "core/company_settings.html", {
        "form": form,
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
                company = Company.objects.create(
                    name=data["company_name"],
                    tax_id=data["tax_id"],
                    address=data["address"],
                    phone=data["phone"],
                    plan="TRIAL",
                    expiration_date=date.today() + timedelta(days=30),
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
                    is_admin=True
                )
                login(request, user)
                return redirect("home")
            except Exception as e:
                form.add_error(None, f"Internal error: {str(e)}")
    else:
        form = SetupForm()

    return render(request, "core/setup_wizard.html", {"form": form})


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
