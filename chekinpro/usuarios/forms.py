from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario
import re

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingresa tu usuario'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Ingresa tu contraseña'})
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            raise forms.ValidationError("❌ El usuario es obligatorio")
        
        # Verificar si el usuario existe en la BD
        if not Usuario.objects.filter(username=username).exists():
            raise forms.ValidationError("❌ Este usuario no existe en la base de datos")
        return username

    def clean_password(self):
        password = self.cleaned_data.get('password')
        username = self.cleaned_data.get('username')
        
        if not password:
            raise forms.ValidationError("❌ La contraseña es obligatoria")
        
        # Solo validar la contraseña si el usuario existe
        if username and Usuario.objects.filter(username=username).exists():
            user = Usuario.objects.get(username=username)
            if not user.check_password(password):
                raise forms.ValidationError("❌ Contraseña incorrecta")
        return password


class RegistroForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'})
    )
    rol = forms.ChoiceField(
        choices=Usuario.ROLES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Usuario
        fields = ('username', 'email', 'rol', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar widgets de password
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Mínimo 8 caracteres'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Repite la contraseña'
        })
        # Eliminar help_text de las contraseñas
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None

    # Validación de usuario
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            raise forms.ValidationError("❌ El usuario es obligatorio")
        if len(username) < 4:
            raise forms.ValidationError("❌ El usuario debe tener al menos 4 caracteres")
        if not re.match(r'^[a-zA-Z0-9@.+-_]+$', username):
            raise forms.ValidationError("❌ El usuario solo puede contener letras, números y @/./+/-/_")
        if Usuario.objects.filter(username=username).exists():
            raise forms.ValidationError("❌ Este usuario ya está registrado")
        return username

    # Validación de email
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("❌ El correo electrónico es obligatorio")
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("❌ Este correo electrónico ya está registrado")
        return email

    # Validación de contraseña
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if not password:
            raise forms.ValidationError("❌ La contraseña es obligatoria")
        if len(password) < 8:
            raise forms.ValidationError("❌ La contraseña debe tener al menos 8 caracteres")
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError("❌ La contraseña debe contener al menos una letra mayúscula")
        if not re.search(r'[0-9]', password):
            raise forms.ValidationError("❌ La contraseña debe contener al menos un número")
        if not re.search(r'[@$!%*?&]', password):
            raise forms.ValidationError("❌ La contraseña debe contener al menos un carácter especial (@$!%*?&)")
        return password

    # Validación de confirmación de contraseña
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if not password2:
            raise forms.ValidationError("❌ Debes confirmar tu contraseña")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("❌ Las contraseñas no coinciden")
        return password2

    # Validación del rol
    def clean_rol(self):
        rol = self.cleaned_data.get('rol')
        if not rol:
            raise forms.ValidationError("❌ Debes seleccionar un rol")
        if rol not in dict(Usuario.ROLES).keys():
            raise forms.ValidationError("❌ Rol no válido")
        return rol

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class ResetPasswordForm(forms.Form):
    username = forms.CharField(
        label="Usuario",
        max_length=150,
        widget=forms.TextInput(attrs={
            "placeholder": "Nombre de usuario",
            "class": "form-control"
        })
    )
    new_password = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Nueva contraseña",
            "class": "form-control"
        })
    )

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if not username:
            raise forms.ValidationError("❌ El usuario es obligatorio")
        if not Usuario.objects.filter(username=username).exists():
            raise forms.ValidationError("❌ Usuario no encontrado en la base de datos.")
        return username

    def clean_new_password(self):
        password = self.cleaned_data.get("new_password")
        if not password:
            raise forms.ValidationError("❌ La nueva contraseña es obligatoria")
        if len(password) < 8:
            raise forms.ValidationError("❌ La contraseña debe tener al menos 8 caracteres.")
        if not re.search(r"[A-Z]", password):
            raise forms.ValidationError("❌ Debe contener al menos una letra mayúscula.")
        if not re.search(r"[0-9]", password):
            raise forms.ValidationError("❌ Debe contener al menos un número.")
        if not re.search(r"[@$!%*?&]", password):
            raise forms.ValidationError("❌ Debe contener al menos un carácter especial (@, $, !, %, *, ?, &).")
        return password