from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Client, Company, UserProfile
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


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'tax_id', 'address', 'phone', 'currency', 'language']
        labels = {
            'name': _('Company Name'),
            'tax_id': _('Tax ID'),
            'address': _('Address'),
            'phone': _('Phone'),
            'currency': _('Currency'),
            'language': _('Language'),
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
        }


class SetupForm(forms.Form):
    username = forms.CharField(label=_("Username"), max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'admin'}))
    email = forms.EmailField(label=_("Email"), widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password_confirm = forms.CharField(label=_("Confirm Password"), widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    company_name = forms.CharField(label=_("Business Name"), max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    tax_id = forms.CharField(label=_("Tax ID"), max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(label=_("Address"), required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(label=_("Phone"), required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password") != cleaned_data.get("password_confirm"):
            raise forms.ValidationError(_("Passwords do not match."))
        return cleaned_data


class EmployeeForm(forms.ModelForm):
    role = forms.ChoiceField(choices=UserProfile.ROLES, widget=forms.Select(attrs={'class': 'form-select'}))
    is_admin = forms.BooleanField(required=False, label=_("Is Administrator?"), widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
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


class EditEmployeeForm(forms.ModelForm):
    role = forms.ChoiceField(choices=UserProfile.ROLES, widget=forms.Select(attrs={'class': 'form-select'}))
    is_admin = forms.BooleanField(required=False, label=_("Administrator permissions"), widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
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
