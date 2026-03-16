from django import forms
from .models import Historial, ArchivoAdjunto, Turno
from core.models import Paciente, UserProfile

class HistorialForm(forms.ModelForm):
    class Meta:
        model = Historial
        fields = ['fecha', 'motivo', 'peso', 'anamnesis', 'diagnostico', 'tratamiento', 'proxima_visita']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.utils import timezone
        ahora = timezone.localtime(timezone.now()).strftime('%Y-%m-%dT%H:%M')
        self.fields['fecha'].widget = forms.DateTimeInput(attrs={
            'class': 'form-control', 'type': 'datetime-local', 'max': ahora
        })
        self.fields['motivo'].widget = forms.TextInput(attrs={'class': 'form-control'})
        self.fields['peso'].widget = forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
        self.fields['anamnesis'].widget = forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        self.fields['diagnostico'].widget = forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        self.fields['tratamiento'].widget = forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        self.fields['proxima_visita'].widget = forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})

# Formulario para subir múltiples archivos (Opcional, por ahora uno simple)
class ArchivoAdjuntoForm(forms.ModelForm):
    # SOBREESCRIBIMOS el campo para que sea opcional
    archivo = forms.FileField(
        required=False,  # <--- ESTO ES LA SOLUCIÓN
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = ArchivoAdjunto
        fields = ['archivo', 'descripcion'] # 'archivo' se usa desde la definición de arriba
        widgets = {
            # 'archivo': ... (Ya lo definimos arriba, así que lo borramos de aquí)
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Radiografía tórax'}),
        }


class TurnoForm(forms.ModelForm):
    class Meta:
        model = Turno
        fields = ['paciente', 'profesional', 'fecha_hora_inicio', 'fecha_hora_fin', 'motivo', 'estado', 'notas']
        widgets = {
            'paciente': forms.Select(attrs={'class': 'form-select'}),
            'profesional': forms.Select(attrs={'class': 'form-select'}),
            'fecha_hora_inicio': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'fecha_hora_fin': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'motivo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Vacunación, Control, Cirugía'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Observaciones adicionales (opcional)'}),
        }

    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa:
            self.fields['paciente'].queryset = Paciente.objects.filter(empresa=empresa)
            self.fields['profesional'].queryset = UserProfile.objects.filter(
                empresa=empresa, rol='VETERINARIO'
            ).select_related('user')

    def clean(self):
        cleaned_data = super().clean()
        inicio = cleaned_data.get('fecha_hora_inicio')
        fin = cleaned_data.get('fecha_hora_fin')
        if inicio and fin and fin <= inicio:
            raise forms.ValidationError('La hora de fin debe ser posterior a la hora de inicio.')
        return cleaned_data