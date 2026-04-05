from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from .models import Usuario
from hotel.models import Hotel
from habitaciones.models import Habitacion
from .forms import LoginForm, RegistroForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.files.base import ContentFile
import base64

@login_required
@require_POST
def subir_foto_perfil(request):
    try:
        data = request.POST.get('profile_picture') or request.FILES.get('profile_picture')
        if not data:
            return JsonResponse({'success': False, 'error': 'No se recibió imagen'})
        
        # Si viene como base64 (desde canvas)
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            file = ContentFile(base64.b64decode(imgstr), name=f"profile_{request.user.id}.{ext}")
            request.user.profile_picture = file
        else:
            # Si viene como archivo directo
            request.user.profile_picture = data
        request.user.save()
        return JsonResponse({'success': True, 'image_url': request.user.profile_picture.url})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def home(request):
    if request.user.is_authenticated:
        return redirect('panel')
    return render(request, 'home.html')


@login_required
@user_passes_test(lambda u: u.rol == 'admin')
def toggle_suspension(request):
    admin_user = request.user
    
    # Obtener el hotel_id de la sesión (o el primer hotel del admin)
    hotel_id = request.session.get('hotel_id')
    if not hotel_id:
        hotel = Hotel.objects.filter(usuario=admin_user).first()
        if hotel:
            hotel_id = hotel.id
        else:
            messages.error(request, "No tienes hoteles asociados.")
            return redirect('mis_hoteles')
    
    # Obtener el hotel específico
    try:
        hotel = Hotel.objects.get(id=hotel_id, usuario=admin_user)
    except Hotel.DoesNotExist:
        messages.error(request, "Hotel no encontrado.")
        return redirect('mis_hoteles')
    
    # Cambiar estado de suspensión del admin
    admin_user.is_suspended = not admin_user.is_suspended
    admin_user.save()
    
    # Buscar recepcionistas de este hotel
    recepcionistas = Usuario.objects.filter(rol='recep', email=hotel.email)
    for recep in recepcionistas:
        recep.is_active = not admin_user.is_suspended
        recep.save()
        
        # Enviar correo (opcional, puedes comentar si no quieres)
        if admin_user.is_suspended:
            subject = f"🔒 Cuenta suspendida - {hotel.nombre}"
            message = f"Hola {recep.username},\n\nEl administrador ha suspendido tu cuenta en el hotel {hotel.nombre}. No podrás acceder hasta nueva orden.\n\nEquipo ChekinPro"
        else:
            subject = f"✅ Cuenta reactivada - {hotel.nombre}"
            message = f"Hola {recep.username},\n\nTu cuenta en el hotel {hotel.nombre} ha sido reactivada. Ya puedes ingresar.\n\nEquipo ChekinPro"
        try:
            send_mail(subject, message, settings.EMAIL_HOST_USER, [recep.email], fail_silently=False)
        except Exception as e:
            print(f"Error enviando correo: {e}")
    
    # Mensaje para mostrar en el panel del hotel
    if admin_user.is_suspended:
        messages.success(request, "🔒 Modo Suspensión Activado. Los recepcionistas han sido desactivados y notificados.")
    else:
        messages.success(request, "✅ Modo Suspensión Desactivado. Los recepcionistas han sido reactivados y notificados.")
    
    # Redirigir al panel del hotel (con el hotel_id)
    return redirect('panel_hotel', hotel_id=hotel.id)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('panel')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)

            if user is not None:
                # Verificar si la cuenta está activa (no suspendida)
                if not user.is_active:
                    messages.error(request,
                        "🚫 **Cuenta suspendida**\n\n"
                        "El administrador del hotel ha desactivado temporalmente tu acceso.\n"
                        "Por favor, contacta con el administrador para más información.\n\n"
                        "— Equipo ChekinPro"
                    )
                    return redirect('login')

                login(request, user)

                if user.rol == 'admin':
                    if Hotel.objects.filter(usuario=user).exists():
                        return redirect('panel')
                    else:
                        return redirect('crear_hotel')
                else:  # recepcionista
                    hotel = Hotel.objects.filter(email=user.email).first()
                    if hotel:
                        request.session['hotel_id'] = hotel.id
                        return redirect('panel')
                    else:
                        messages.error(request,
                            "❌ No tienes un hotel asignado. Contacta al administrador del sistema."
                        )
                        return redirect('logout')
            else:
                form.add_error('password', '❌ Contraseña incorrecta')
    else:
        form = LoginForm()

    return render(request, 'usuarios/login.html', {'form': form})

def registro(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        is_admin = request.POST.get('is_admin') == 'on'
        
        if not username or not email or not password1:
            messages.error(request, "❌ Todos los campos son obligatorios")
            return render(request, "usuarios/registro.html")
        
        if password1 != password2:
            messages.error(request, "❌ Las contraseñas no coinciden")
            return render(request, "usuarios/registro.html")
        
        if len(password1) < 8:
            messages.error(request, "❌ La contraseña debe tener al menos 8 caracteres")
            return render(request, "usuarios/registro.html")
        
        if Usuario.objects.filter(username=username).exists():
            messages.error(request, "❌ El nombre de usuario ya existe")
            return render(request, "usuarios/registro.html")
        
        if Usuario.objects.filter(email=email).exists():
            messages.error(request, "❌ El email ya está registrado")
            return render(request, "usuarios/registro.html")
        
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
            return redirect('login')
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
            reset_link = f"{settings.SITE_URL}/reset/{uid}/{token}/"
            
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

def saber_mas(request):
    return render(request, 'saber_mas.html')

# ===================== VISTAS PRIVADAS (requieren login) =====================

@login_required
def panel(request):
    if request.user.rol == 'admin':
        hoteles = Hotel.objects.filter(usuario=request.user)
        for hotel in hoteles:
            habitaciones = Habitacion.objects.filter(hotel=hotel)
            hotel.total_habitaciones = habitaciones.count()
            hotel.ocupadas = habitaciones.filter(estado='ocupada').count()
            hotel.libres = habitaciones.filter(estado='libre').count()
            hotel.mantenimiento = habitaciones.filter(estado='mantenimiento').count()
        return render(request, 'panel_admin.html', {'hoteles': hoteles})
    else:
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
    user = request.user
    if request.method == 'POST':
        # Eliminar foto
        if 'delete_photo' in request.POST:
            if user.profile_picture:
                # Borrar el archivo físico
                user.profile_picture.delete(save=False)
                user.profile_picture = None
                user.save()
                messages.success(request, "✅ Foto de perfil eliminada correctamente.")
            else:
                messages.warning(request, "No tienes una foto de perfil para eliminar.")
            return redirect('mi_perfil')
        
        # Actualizar datos normales y posible nueva foto
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.email = request.POST.get('email', '').strip()
        user.telefono = request.POST.get('telefono', '').strip()
        
        if 'profile_picture' in request.FILES:
            # Si ya había foto, la borramos físicamente antes de asignar nueva
            if user.profile_picture:
                user.profile_picture.delete(save=False)
            user.profile_picture = request.FILES['profile_picture']
        
        user.save()
        messages.success(request, "✅ Perfil actualizado correctamente.")
        return redirect('mi_perfil')
    
    return render(request, 'usuarios/perfil.html', {'usuario': user})

@login_required
def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def configuracion(request):
    return render(request, 'usuarios/configuracion.html', {'usuario': request.user})



