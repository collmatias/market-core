from django import forms
from .models import Historial, ArchivoAdjunto

class HistorialForm(forms.ModelForm):
    class Meta:
        model = Historial
        fields = ['fecha', 'motivo', 'peso', 'anamnesis', 'diagnostico', 'tratamiento', 'proxima_visita']
        widgets = {
            'fecha': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'motivo': forms.TextInput(attrs={'class': 'form-control'}),
            'peso': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'anamnesis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'diagnostico': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tratamiento': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'proxima_visita': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

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