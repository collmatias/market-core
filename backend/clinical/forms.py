from django import forms
from django.utils.translation import gettext_lazy as _
from .models import MedicalRecord, Attachment, Appointment
from core.models import Patient, UserProfile


class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ['date', 'reason', 'weight', 'anamnesis', 'diagnosis', 'treatment', 'next_visit']
        labels = {
            'date': _('Date'),
            'reason': _('Reason'),
            'weight': _('Weight (kg)'),
            'anamnesis': _('Anamnesis / Notes'),
            'diagnosis': _('Diagnosis'),
            'treatment': _('Treatment / Instructions'),
            'next_visit': _('Next Visit'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.utils import timezone
        now = timezone.localtime(timezone.now()).strftime('%Y-%m-%dT%H:%M')
        self.fields['date'].widget = forms.DateTimeInput(attrs={
            'class': 'form-control', 'type': 'datetime-local', 'max': now
        })
        self.fields['reason'].widget = forms.TextInput(attrs={'class': 'form-control'})
        self.fields['weight'].widget = forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
        self.fields['anamnesis'].widget = forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        self.fields['diagnosis'].widget = forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        self.fields['treatment'].widget = forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        self.fields['next_visit'].widget = forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})


class AttachmentForm(forms.ModelForm):
    file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Attachment
        fields = ['file', 'description']
        labels = {
            'description': _('Description'),
        }
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control'}),
        }


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['patient', 'professional', 'start_time', 'end_time', 'reason', 'status', 'notes']
        labels = {
            'patient': _('Patient'),
            'professional': _('Professional'),
            'start_time': _('Start Time'),
            'end_time': _('End Time'),
            'reason': _('Reason'),
            'status': _('Status'),
            'notes': _('Notes'),
        }
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select'}),
            'professional': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'reason': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            self.fields['patient'].queryset = Patient.objects.filter(company=company)
            self.fields['professional'].queryset = UserProfile.objects.filter(
                company=company, role='VET'
            )
