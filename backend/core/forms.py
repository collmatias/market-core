from django import forms
from .models import Cliente, Paciente, Empresa, UserProfile
from django.contrib.auth.models import User

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'telefono', 'email', 'direccion']
        # Esto es para que se vea bonito con Bootstrap
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
        }

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ['cliente', 'nombre', 'especie', 'raza', 'fecha_nacimiento', 'peso_actual']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}), # Select estilizado
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'especie': forms.Select(attrs={'class': 'form-select'}),
            'raza': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), # Calendario
            'peso_actual': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['nombre', 'cuit', 'direccion', 'telefono'] # Agrega los campos que tengas en el modelo
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Veterinaria Patitas'}),
            'cuit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'XX-XXXXXXXX-X'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }

class SetupForm(forms.Form):
    # --- DATOS DEL ADMIN (Dueño) ---
    username = forms.CharField(label="Nombre de Usuario", max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: admin'}))
    email = forms.EmailField(label="Correo Electrónico", widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'tu@email.com'}))
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password_confirm = forms.CharField(label="Confirmar Contraseña", widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    # --- DATOS DE LA VETERINARIA ---
    nombre_empresa = forms.CharField(label="Nombre de la Veterinaria", max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    cuit = forms.CharField(label="CUIT", max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '20-xxxxxxxx-x'}))
    direccion = forms.CharField(label="Dirección", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    telefono = forms.CharField(label="Teléfono", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password != password_confirm:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data

class EmpleadoForm(forms.ModelForm):
    # Campos extra que no están en User directo
    rol = forms.ChoiceField(choices=UserProfile.ROLES, label="Rol / Permisos", widget=forms.Select(attrs={'class': 'form-select'}))
    matricula = forms.CharField(required=False, label="Matrícula Profesional", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional'}))
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class EditarEmpleadoForm(forms.ModelForm):
    rol = forms.ChoiceField(choices=UserProfile.ROLES, label="Rol / Permisos", widget=forms.Select(attrs={'class': 'form-select'}))
    matricula = forms.CharField(required=False, label="Matrícula Profesional", widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
