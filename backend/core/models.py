from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class TenantManager(models.Manager):
    def for_company(self, user):
        return self.get_queryset().filter(company=user.profile.company)


class Company(models.Model):
    CURRENCIES = [
        ('ARS', _('Argentine Peso ($)')),
        ('USD', _('US Dollar (US$)')),
        ('EUR', _('Euro (€)')),
        ('BRL', _('Brazilian Real (R$)')),
        ('CLP', _('Chilean Peso (CLP$)')),
        ('MXN', _('Mexican Peso (MX$)')),
        ('UYU', _('Uruguayan Peso ($U)')),
        ('PYG', _('Paraguayan Guarani (₲)')),
        ('COP', _('Colombian Peso (COL$)')),
        ('PEN', _('Peruvian Sol (S/)')),
        ('BOB', _('Bolivian Boliviano (Bs)')),
    ]

    LANGUAGES = [
        ('es', _('Spanish')),
        ('en', _('English')),
        ('pt', _('Portuguese')),
    ]

    name = models.CharField(max_length=100)
    tax_id = models.CharField(max_length=20, unique=True)
    address = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    currency = models.CharField(max_length=3, choices=CURRENCIES, default='ARS')
    language = models.CharField(max_length=5, choices=LANGUAGES, default='es')

    # SaaS license data
    plan = models.CharField(max_length=20, default='FREE')
    expiration_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'companies'

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    ROLES = [
        ('VET', _('Veterinarian')),
        ('ADMIN', _('Administrative')),
    ]

    AVATARS = [
        ('bi-person-fill', '👤 Default'),
        ('bi-person-circle', '🧑‍💼 Classic'),
        ('bi-emoji-sunglasses-fill', '😎 Sunglasses'),
        ('bi-emoji-smile-fill', '😊 Smiley'),
        ('bi-robot', '🤖 Robot'),
        ('bi-stars', '✨ Stars'),
        ('bi-heart-pulse-fill', '💖 Heart'),
        ('bi-capsule', '💊 Capsule'),
        ('bi-bandaid-fill', '🩹 Bandaid'),
        ('bi-bug-fill', '🐞 Bug'),
        ('bi-controller', '🎮 Gamer'),
        ('bi-moon-stars-fill', '🌙 Moon'),
        ('bi-cup-hot-fill', '☕ Coffee'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    role = models.CharField(max_length=20, choices=ROLES, default='VET')
    is_admin = models.BooleanField(default=False)
    license_number = models.CharField(max_length=50, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    pin = models.CharField(max_length=4, blank=True, null=True)
    avatar = models.CharField(max_length=50, choices=AVATARS, default='bi-person-fill')

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

    @property
    def is_clinical(self):
        return self.role == 'VET'


class Client(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = TenantManager()

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"


class Patient(models.Model):
    SPECIES = [
        ('DOG', _('Dog')),
        ('CAT', _('Cat')),
        ('OTHER', _('Other')),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    owner = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='pets')
    name = models.CharField(max_length=50)
    species = models.CharField(max_length=10, choices=SPECIES)
    breed = models.CharField(max_length=50, blank=True)
    birth_date = models.DateField(blank=True, null=True)
    current_weight = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    objects = TenantManager()

    def __str__(self):
        return f"{self.name} ({self.get_species_display()})"
