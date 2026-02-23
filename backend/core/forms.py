from django import forms
from .models import Cliente, Paciente, Empresa, UserProfile
from django.contrib.auth.models import User

class AdminSetPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label="Nueva Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Ingresa la nueva clave (sin restricciones de longitud ni seguridad)."
    )
    new_password2 = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Repite la contraseña para confirmar."
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password1')
        p2 = cleaned_data.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden. Intenta de nuevo.")
        return cleaned_data

class CambiarPinForm(forms.Form):
    nuevo_pin = forms.CharField(
        label="Nuevo PIN",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control text-center fs-4', 
            'maxlength': '4', 
            'placeholder': '••••',
            'pattern': '[0-9]*',
            'inputmode': 'numeric'
        }),
        help_text="Debe contener exactamente 4 números."
    )
    confirmar_pin = forms.CharField(
        label="Confirmar Nuevo PIN",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control text-center fs-4', 
            'maxlength': '4', 
            'placeholder': '••••',
            'pattern': '[0-9]*',
            'inputmode': 'numeric'
        }),
        help_text="Repite el PIN para confirmarlo."
    )

    def clean(self):
        cleaned_data = super().clean()
        pin1 = cleaned_data.get('nuevo_pin')
        pin2 = cleaned_data.get('confirmar_pin')

        if pin1 and pin2:
            if pin1 != pin2:
                raise forms.ValidationError("Los PINs no coinciden. Inténtalo de nuevo.")
            if not pin1.isdigit() or len(pin1) != 4:
                raise forms.ValidationError("El PIN debe ser estrictamente numérico y de 4 dígitos.")
        return cleaned_data

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
    rol = forms.ChoiceField(choices=UserProfile.ROLES, widget=forms.Select(attrs={'class': 'form-select'}))
    es_admin = forms.BooleanField(required=False, label="¿Es Administrador?", widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    matricula = forms.CharField(required=False, label="Matrícula Profesional", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional'}))
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    pin = forms.CharField(required=False, label="PIN Rápido (4 dígitos)", widget=forms.PasswordInput(attrs={'class': 'form-control', 'maxlength': '4', 'placeholder': 'Ej: 1234'}))
    avatar = forms.ChoiceField(choices=UserProfile.AVATARES, label="Icono de Perfil", widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        # Primero dejamos que Django haga sus validaciones normales
        cleaned_data = super().clean()
        
        # Obtenemos lo que el usuario seleccionó/escribió
        rol = cleaned_data.get('rol')
        matricula = cleaned_data.get('matricula')

        # La regla de oro: Si es Vete y no hay matrícula, lanzamos error
        if rol == 'VETERINARIO' and not matricula:
            self.add_error('matricula', 'La matrícula profesional es obligatoria para los Veterinarios.')
            
        return cleaned_data

class EditarEmpleadoForm(forms.ModelForm):
    rol = forms.ChoiceField(choices=UserProfile.ROLES, widget=forms.Select(attrs={'class': 'form-select'}))
    es_admin = forms.BooleanField(required=False, label="Dar permisos de Administrador", widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    matricula = forms.CharField(required=False, label="Matrícula Profesional", widget=forms.TextInput(attrs={'class': 'form-control'}))
    pin = forms.CharField(required=False, label="PIN de Acceso Rápido (4 dígitos)", widget=forms.TextInput(attrs={'class': 'form-control', 'maxlength': '4', 'type': 'password'}))
    avatar = forms.ChoiceField(choices=UserProfile.AVATARES, label="Icono de Perfil", widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        
        rol = cleaned_data.get('rol')
        matricula = cleaned_data.get('matricula')

        # Limpiamos espacios en blanco por si tipearion "   "
        if matricula:
            matricula = matricula.strip()

        # Si es Veterinario y la matrícula está vacía (o eran solo espacios)
        if rol == 'VETERINARIO' and not matricula:
            # Esto bloquea el guardado y enciende la alarma en el campo 'matricula'
            self.add_error('matricula', 'La matrícula es obligatoria.')
            
        return cleaned_data