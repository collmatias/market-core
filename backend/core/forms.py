from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Client, Patient, Company, UserProfile
from django.contrib.auth.models import User


class AdminSetPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label=_("New Password"),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    new_password2 = forms.CharField(
        label=_("Confirm Password"),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password1')
        p2 = cleaned_data.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError(_("Passwords do not match."))
        return cleaned_data


class ChangePinForm(forms.Form):
    new_pin = forms.CharField(
        label=_("New PIN"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control text-center fs-4',
            'maxlength': '4',
            'placeholder': '••••',
            'pattern': '[0-9]*',
            'inputmode': 'numeric'
        }),
    )
    confirm_pin = forms.CharField(
        label=_("Confirm PIN"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control text-center fs-4',
            'maxlength': '4',
            'placeholder': '••••',
            'pattern': '[0-9]*',
            'inputmode': 'numeric'
        }),
    )

    def clean(self):
        cleaned_data = super().clean()
        pin1 = cleaned_data.get('new_pin')
        pin2 = cleaned_data.get('confirm_pin')
        if pin1 and pin2:
            if pin1 != pin2:
                raise forms.ValidationError(_("PINs do not match."))
            if not pin1.isdigit() or len(pin1) != 4:
                raise forms.ValidationError(_("PIN must be exactly 4 digits."))
        return cleaned_data


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['first_name', 'last_name', 'phone', 'email', 'address']
        labels = {
            'first_name': _('First Name'),
            'last_name': _('Last Name'),
            'phone': _('Phone'),
            'email': _('Email'),
            'address': _('Address'),
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
        }


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['owner', 'name', 'species', 'breed', 'birth_date', 'current_weight']
        labels = {
            'owner': _('Owner'),
            'name': _('Name'),
            'species': _('Species'),
            'breed': _('Breed'),
            'birth_date': _('Birth Date'),
            'current_weight': _('Weight (kg)'),
        }
        widgets = {
            'owner': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'species': forms.Select(attrs={'class': 'form-select'}),
            'breed': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'current_weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class CompanyForm(forms.ModelForm):
    """Full company form — used only during initial setup or by owner admin."""
    class Meta:
        model = Company
        fields = ['name', 'tax_id', 'address', 'phone', 'email', 'currency', 'language']
        labels = {
            'name': _('Company Name'),
            'tax_id': _('Tax ID'),
            'address': _('Address'),
            'phone': _('Phone'),
            'email': _('Company Email'),
            'currency': _('Currency'),
            'language': _('Language'),
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
        }


class CompanySettingsForm(forms.ModelForm):
    """Post-setup settings form — only editable fields (currency, language)."""
    class Meta:
        model = Company
        fields = ['currency', 'language']
        labels = {
            'currency': _('Currency'),
            'language': _('Language'),
        }
        widgets = {
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
        }


class SetupForm(forms.Form):
    # Admin user fields
    username = forms.CharField(label=_('Username'), max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'admin'}))
    email = forms.EmailField(label=_('Admin Email'), widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label=_('Password'), widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password_confirm = forms.CharField(label=_('Confirm Password'), widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    # Company identity fields (immutable after setup)
    company_name = forms.CharField(label=_('Clinic Name'), max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    tax_id = forms.CharField(label=_('Tax ID'), max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    company_email = forms.EmailField(label=_('Clinic Email'), widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(label=_('Phone'), max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(label=_('Address'), required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('password') != cleaned_data.get('password_confirm'):
            raise forms.ValidationError(_('Passwords do not match.'))
        return cleaned_data


class RegistrationForm(forms.Form):
    """SaaS public registration form. account_type is set by the URL, not by the user."""
    # Account
    username = forms.CharField(label=_('Username'), max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'admin'}))
    email = forms.EmailField(label=_('Email'), widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label=_('Password'), min_length=8, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password_confirm = forms.CharField(label=_('Confirm Password'), widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    # Company
    company_name = forms.CharField(label=_('Company Name'), max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    tax_id = forms.CharField(label=_('Tax ID'), max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    company_email = forms.EmailField(label=_('Company Email'), widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(label=_('Phone'), max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(label=_('Address'), required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    region = forms.CharField(label=_('Region'), max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('e.g. AR-CBA')}))

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(_('This username is already taken.'))
        return username

    def clean_email(self):
        return self.cleaned_data['email']

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('password') != cleaned_data.get('password_confirm'):
            raise forms.ValidationError(_('Passwords do not match.'))
        return cleaned_data


class EmployeeForm(forms.ModelForm):
    role = forms.ChoiceField(choices=UserProfile.ROLES, widget=forms.Select(attrs={'class': 'form-select'}))
    is_admin = forms.BooleanField(required=False, label=_("Is Administrator?"), widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    license_number = forms.CharField(required=False, label=_("License Number"), widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    pin = forms.CharField(required=False, label=_("Quick PIN (4 digits)"), widget=forms.PasswordInput(attrs={'class': 'form-control', 'maxlength': '4'}))
    avatar = forms.ChoiceField(choices=UserProfile.AVATARS, label=_("Profile Icon"), widget=forms.Select(attrs={'class': 'form-select'}))

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
        if cleaned_data.get('role') == 'VET' and not cleaned_data.get('license_number'):
            self.add_error('license_number', _('License number is required for veterinarians.'))
        return cleaned_data


class EditEmployeeForm(forms.ModelForm):
    role = forms.ChoiceField(choices=UserProfile.ROLES, widget=forms.Select(attrs={'class': 'form-select'}))
    is_admin = forms.BooleanField(required=False, label=_("Administrator permissions"), widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    license_number = forms.CharField(required=False, label=_("License Number"), widget=forms.TextInput(attrs={'class': 'form-control'}))
    pin = forms.CharField(required=False, label=_("Quick Access PIN (4 digits)"), widget=forms.TextInput(attrs={'class': 'form-control', 'maxlength': '4', 'type': 'password'}))
    avatar = forms.ChoiceField(choices=UserProfile.AVATARS, label=_("Profile Icon"), widget=forms.Select(attrs={'class': 'form-select'}))

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
        license_number = cleaned_data.get('license_number', '').strip()
        if cleaned_data.get('role') == 'VET' and not license_number:
            self.add_error('license_number', _('License number is required.'))
        return cleaned_data
