from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from .models import Usuario
from hotel.models import Hotel
from habitaciones.models import Habitacion
from .forms import LoginForm, RegistroForm
from reservas.models import Reserva


def home(request):
    if request.user.is_authenticated:
        return redirect('panel')
    return render(request, 'home.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('panel')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            user = authenticate(request, username=username, password=password)
            
            if user:
                login(request, user)
                
                # Si es admin, redirigir según tenga hotel o no
                if user.rol == 'admin':
                    try:
                        hotel = user.hotel
                        return redirect('panel')
                    except:
                        return redirect('crear_hotel')
                else:
                    # Si es recepcionista, buscar el hotel por email
                    from hotel.models import Hotel
                    hotel = Hotel.objects.filter(email=user.email).first()
                    
                    if hotel:
                        request.session['hotel_id'] = hotel.id
                        return redirect('panel')
                    else:
                        messages.error(request, "No tienes un hotel asignado. Contacta al administrador.")
                        return redirect('logout')
            else:
                # Contraseña incorrecta
                form.add_error('password', '❌ Contraseña incorrecta')
    else:
        form = LoginForm()
    
    return render(request, 'usuarios/login.html', {'form': form})


@login_required
def panel(request):
    if request.user.rol == 'admin':
        # Admin: ver lista de hoteles
        hoteles = Hotel.objects.filter(usuario=request.user)
        
        # Calcular estadísticas
        for hotel in hoteles:
            habitaciones = Habitacion.objects.filter(hotel=hotel)
            hotel.total_habitaciones = habitaciones.count()
            hotel.ocupadas = habitaciones.filter(estado='ocupada').count()
            hotel.libres = habitaciones.filter(estado='libre').count()
            hotel.mantenimiento = habitaciones.filter(estado='mantenimiento').count()
        
        return render(request, 'panel_admin.html', {'hoteles': hoteles})
    
    else:  # recepcionista
        hotel = Hotel.objects.filter(email=request.user.email).first()
        
        if not hotel:
            messages.error(request, "No tienes un hotel asignado")
            return redirect('login')
        
        habitaciones = Habitacion.objects.filter(hotel=hotel)
        
        context = {
            'hotel': hotel,
            'total_habitaciones': habitaciones.count(),
            'libres': habitaciones.filter(estado='libre').count(),
            'ocupadas': habitaciones.filter(estado='ocupada').count(),
            'mantenimiento': habitaciones.filter(estado='mantenimiento').count(),
        }
        return render(request, 'panel_recepcionista.html', context)
        
@login_required
def mi_perfil(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.telefono = request.POST.get('telefono', '')
        user.save()
        messages.success(request, "✅ Perfil actualizado correctamente")
        return redirect('mi_perfil')

    return render(request, 'usuarios/perfil.html', {'usuario': request.user})


@login_required
def logout_view(request):
    logout(request)
    return redirect('home')

def registro(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        is_admin = request.POST.get('is_admin') == 'on'
        
        # Validaciones
        if not username or not email or not password1:
            messages.error(request, "❌ Todos los campos son obligatorios")
            return render(request, "usuarios/registro.html")
        
        if password1 != password2:
            messages.error(request, "❌ Las contraseñas no coinciden")
            return render(request, "usuarios/registro.html")
        
        if len(password1) < 8:
            messages.error(request, "❌ La contraseña debe tener al menos 8 caracteres")
            return render(request, "usuarios/registro.html")
        
        # Validar si el usuario ya existe
        if Usuario.objects.filter(username=username).exists():
            messages.error(request, "❌ El nombre de usuario ya existe")
            return render(request, "usuarios/registro.html")
        
        if Usuario.objects.filter(email=email).exists():
            messages.error(request, "❌ El email ya está registrado")
            return render(request, "usuarios/registro.html")
        
        # Crear usuario
        rol = 'admin' if is_admin else 'recep'
        
        try:
            user = Usuario.objects.create_user(
                username=username,
                email=email,
                password=password1,
                rol=rol
            )
            user.save()
            
            messages.success(request, "✅ Cuenta creada correctamente. Ahora puedes iniciar sesión.")
            return redirect('login')  # 👈 REDIRIGE AL LOGIN
            
        except Exception as e:
            messages.error(request, f"❌ Error al crear usuario: {str(e)}")
            return render(request, "usuarios/registro.html")
    
    return render(request, "usuarios/registro.html")


def recuperar_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = Usuario.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            reset_link = f"{settings.SITE_URL}/reset-password/{uid}/{token}/"

            send_mail(
                "Recupera tu contraseña - ChekinPro",
                f"Haz clic en el siguiente enlace para recuperar tu contraseña:\n\n{reset_link}",
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
            messages.success(request, "📧 Revisa tu correo para recuperar tu contraseña")
            return redirect('login')
        except Usuario.DoesNotExist:
            messages.error(request, "❌ No existe una cuenta con ese correo")

    return render(request, 'recuperar.html')


def reset_password_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Usuario.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password = request.POST.get('password')
            confirm = request.POST.get('confirm_password')

            if password and password == confirm and len(password) >= 8:
                user.set_password(password)
                user.save()
                messages.success(request, "✅ Contraseña actualizada correctamente")
                return redirect('login')
            else:
                messages.error(request, "❌ Las contraseñas no coinciden o son muy cortas")

        return render(request, 'reset_confirm.html', {'valid': True})
    else:
        messages.error(request, "❌ El enlace no es válido o ha expirado")
        return redirect('recuperar_password')


@login_required
def configuracion(request):
    return render(request, 'usuarios/configuracion.html', {'usuario': request.user})

def saber_mas(request):
    return render(request, 'saber_mas.html')

def recuperar_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = Usuario.objects.get(email=email)
            
            # Generar token y uid
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Crear enlace de recuperación
            reset_link = f"{settings.SITE_URL}/reset/{uid}/{token}/"
            
            # Enviar correo
            send_mail(
                "🔐 Recuperación de contraseña - ChekinPro",
                f"""
                Hola {user.username},
                
                Has solicitado recuperar tu contraseña.
                
                Haz clic en el siguiente enlace para crear una nueva contraseña:
                {reset_link}
                
                Si no solicitaste esto, ignora este correo.
                
                Saludos,
                Equipo ChekinPro
                """,
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
            
            messages.success(request, "📧 Revisa tu correo. Te enviamos un enlace para recuperar tu contraseña.")
            return redirect('login')
            
        except Usuario.DoesNotExist:
            messages.error(request, "❌ No existe una cuenta con ese correo electrónico.")
    
    return render(request, 'recuperar.html')


def reset_password_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Usuario.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
        user = None
    
    if user and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password = request.POST.get('password')
            confirm = request.POST.get('confirm_password')
            
            if password and password == confirm and len(password) >= 8:
                user.set_password(password)
                user.save()
                messages.success(request, "✅ Contraseña actualizada correctamente. Ahora puedes iniciar sesión.")
                return redirect('login')
            else:
                messages.error(request, "❌ Las contraseñas no coinciden o son muy cortas (mínimo 8 caracteres).")
        
        return render(request, 'reset_confirm.html', {'valid': True, 'user': user})
    else:
        messages.error(request, "❌ El enlace no es válido o ha expirado. Solicita uno nuevo.")
        return redirect('recuperar_password')
