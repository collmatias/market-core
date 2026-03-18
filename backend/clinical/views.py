from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from django.utils.translation import gettext as _
from core.models import Patient, UserProfile
from .models import MedicalRecord, Appointment
from .forms import MedicalRecordForm, AttachmentForm, AppointmentForm
from core.decorators import clinical_required
import json


@login_required
def medical_record(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    history = patient.medical_history.all().order_by("-date")
    appointments = patient.appointments.exclude(status__in=["CANCELLED", "COMPLETED"]).order_by("start_time").select_related("professional__user")

    return render(request, "clinical/medical_record.html", {
        "patient": patient,
        "history": history,
        "appointments": appointments,
    })


@login_required
@clinical_required
def new_consultation(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)

    if request.method == "POST":
        form = MedicalRecordForm(request.POST)
        attachment_form = AttachmentForm(request.POST, request.FILES)

        if form.is_valid():
            consultation = form.save(commit=False)
            consultation.patient = patient
            consultation.save()

            if attachment_form.is_valid() and request.FILES.get("file"):
                attachment = attachment_form.save(commit=False)
                attachment.record = consultation
                attachment.save()

            return redirect("medical_record", patient_id=patient.id)
    else:
        form = MedicalRecordForm(initial={"weight": patient.current_weight, "date": timezone.now()})
        attachment_form = AttachmentForm()

    return render(request, "clinical/new_consultation.html", {
        "form": form,
        "attachment_form": attachment_form,
        "patient": patient
    })


@login_required
@clinical_required
def edit_consultation(request, consultation_id):
    consultation = get_object_or_404(MedicalRecord, pk=consultation_id)
    patient = consultation.patient

    if request.method == "POST":
        form = MedicalRecordForm(request.POST, instance=consultation)
        attachment_form = AttachmentForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            if attachment_form.is_valid() and request.FILES.get("file"):
                attachment = attachment_form.save(commit=False)
                attachment.record = consultation
                attachment.save()
            return redirect("medical_record", patient_id=patient.id)
    else:
        form = MedicalRecordForm(instance=consultation)
        attachment_form = AttachmentForm()

    return render(request, "clinical/new_consultation.html", {
        "form": form,
        "attachment_form": attachment_form,
        "patient": patient,
        "is_edit": True
    })


# =============================================================================
# APPOINTMENT / SCHEDULE MODULE
# =============================================================================

@login_required
def schedule(request):
    company = request.user.profile.company
    veterinarians = UserProfile.objects.filter(
        company=company, role="VET"
    ).select_related("user")
    patients = Patient.objects.filter(company=company).select_related("owner")

    preselect_patient = request.GET.get("patient", "")
    preselect_client = request.GET.get("client", "")

    return render(request, "clinical/schedule.html", {
        "veterinarians": veterinarians,
        "patients": patients,
        "preselect_patient": preselect_patient,
        "preselect_client": preselect_client,
    })


@login_required
@require_GET
def api_appointments(request):
    company = request.user.profile.company
    start = request.GET.get("start")
    end = request.GET.get("end")

    appointments = Appointment.objects.filter(company=company).select_related("patient", "professional__user")

    if start:
        appointments = appointments.filter(start_time__gte=start)
    if end:
        appointments = appointments.filter(end_time__lte=end)

    events = []
    for a in appointments:
        events.append({
            "id": a.id,
            "title": f"{a.patient.name} - {a.reason}",
            "start": a.start_time.isoformat(),
            "end": a.end_time.isoformat(),
            "color": a.color,
            "extendedProps": {
                "patient_id": a.patient.id,
                "professional_id": a.professional.id,
                "professional_name": a.professional.user.get_full_name() or a.professional.user.username,
                "reason": a.reason,
                "status": a.status,
                "notes": a.notes,
            }
        })

    return JsonResponse(events, safe=False)


@login_required
@require_POST
def create_appointment(request):
    company = request.user.profile.company

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Invalid JSON."}, status=400)

    form = AppointmentForm(data, company=company)
    if form.is_valid():
        appointment = form.save(commit=False)
        appointment.company = company
        appointment.save()
        return JsonResponse({
            "ok": True,
            "appointment": {
                "id": appointment.id,
                "title": f"{appointment.patient.name} - {appointment.reason}",
                "start": appointment.start_time.isoformat(),
                "end": appointment.end_time.isoformat(),
                "color": appointment.color,
            }
        })
    else:
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)


@login_required
@require_POST
def edit_appointment(request, appointment_id):
    company = request.user.profile.company
    appointment = get_object_or_404(Appointment, pk=appointment_id, company=company)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Invalid JSON."}, status=400)

    form = AppointmentForm(data, instance=appointment, company=company)
    if form.is_valid():
        form.save()
        return JsonResponse({
            "ok": True,
            "appointment": {
                "id": appointment.id,
                "title": f"{appointment.patient.name} - {appointment.reason}",
                "start": appointment.start_time.isoformat(),
                "end": appointment.end_time.isoformat(),
                "color": appointment.color,
            }
        })
    else:
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)


@login_required
@require_POST
def cancel_appointment(request, appointment_id):
    company = request.user.profile.company
    appointment = get_object_or_404(Appointment, pk=appointment_id, company=company)
    appointment.status = "CANCELLED"
    appointment.save()
    return JsonResponse({"ok": True, "color": appointment.color})


@login_required
@require_POST
def complete_appointment(request, appointment_id):
    company = request.user.profile.company
    appointment = get_object_or_404(Appointment, pk=appointment_id, company=company)
    appointment.status = "COMPLETED"
    appointment.save()

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = {}

    create_record = data.get("create_record", False)
    record_id = None

    if create_record:
        record = MedicalRecord.objects.create(
            patient=appointment.patient,
            reason=appointment.reason,
            anamnesis=appointment.notes,
        )
        record_id = record.id

    return JsonResponse({
        "ok": True,
        "color": appointment.color,
        "record_id": record_id,
        "patient_id": appointment.patient.id,
    })
