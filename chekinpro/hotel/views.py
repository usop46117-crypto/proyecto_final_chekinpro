from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Hotel
from habitaciones.models import Habitacion
from reservas.models import Reserva
from usuarios.models import Usuario
from .forms import HotelForm
import random
import string
from django.core.mail import send_mail
from django.conf import settings

@login_required
def crear_hotel(request):
    # Solo administradores pueden crear hoteles
    if request.user.rol != 'admin':
        messages.error(request, "⛔ Solo administradores pueden crear hoteles")
        return redirect('panel')

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        direccion = request.POST.get('direccion', '')
        telefono = request.POST.get('telefono', '')
        email_recep = request.POST.get('email', '')  # Email del recepcionista
        logo = request.FILES.get('logo')
        tiene_parqueadero = request.POST.get('tiene_parqueadero') == 'on'

        # Validar campos obligatorios
        if not nombre or not direccion or not telefono or not email_recep:
            messages.error(request, "Todos los campos son obligatorios")
            return render(request, 'hotel/crear.html')

        # 👇 VALIDACIÓN 1: Nombre de hotel único para este administrador
        if Hotel.objects.filter(usuario=request.user, nombre=nombre).exists():
            messages.error(request, f"❌ Ya tienes un hotel con el nombre '{nombre}'")
            return render(request, 'hotel/crear.html')

        # 👇 VALIDACIÓN 2: Email del recepcionista único en todo el sistema
        if Usuario.objects.filter(email=email_recep).exists():
            messages.error(request, f"❌ El email '{email_recep}' ya está siendo usado por otro usuario")
            return render(request, 'hotel/crear.html')

        # Crear hotel
        hotel = Hotel.objects.create(
            usuario=request.user,
            nombre=nombre,
            direccion=direccion,
            telefono=telefono,
            email=email_recep,  # Guardamos el email del recepcionista
            logo=logo,
            tiene_parqueadero=tiene_parqueadero
        )

        # Crear recepcionista automático
        username = f"recep_{hotel.id}_{''.join(random.choices(string.ascii_lowercase, k=4))}"
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

        recepcionista = Usuario.objects.create(
            username=username,
            email=email_recep,
            rol='recep',
            first_name=f"Recepcionista {hotel.nombre}"
        )
        recepcionista.set_password(password)
        recepcionista.save()

        # Enviar credenciales por correo
        try:
            send_mail(
                f"Credenciales de acceso - {hotel.nombre}",
                f"""
                Hola,

                Se ha creado un usuario para ti en el hotel {hotel.nombre}.

                Usuario: {username}
                Contraseña: {password}

                Puedes iniciar sesión en: {settings.SITE_URL}/login/

                Saludos,
                Equipo ChekinPro
                """,
                settings.EMAIL_HOST_USER,
                [email_recep],
                fail_silently=False,
            )
        except Exception as e:
            messages.warning(request, f"Hotel creado pero no se pudo enviar el correo: {str(e)}")

        messages.success(request, f"✅ Hotel '{nombre}' creado correctamente")
        return redirect('panel')  # ✅ Redirige al panel principal

    return render(request, 'hotel/crear.html')


@login_required
def mis_hoteles(request):
    if request.user.rol != 'admin':
        messages.error(request, "Solo administradores pueden ver esta página")
        return redirect('panel')  # ✅ Redirige al panel principal
    
    hoteles = Hotel.objects.filter(usuario=request.user)
    
    # Agregar el recepcionista a cada hotel
    for hotel in hoteles:
        if hotel.email:
            hotel.recepcionista = Usuario.objects.filter(email=hotel.email, rol='recep').first()
        else:
            hotel.recepcionista = None
    
    return render(request, 'hotel/mis_hoteles.html', {'hoteles': hoteles})


@login_required
def dashboard(request):
    if request.user.rol == 'recep':
        hotel = Hotel.objects.filter(email=request.user.email).first()
    else:
        hotel = request.user.hotel

    if not hotel:
        return redirect('crear_hotel')

    habitaciones = Habitacion.objects.filter(hotel=hotel)

    context = {
        'total': habitaciones.count(),
        'libres': habitaciones.filter(estado='libre').count(),
        'ocupadas': habitaciones.filter(estado='ocupada').count(),
        'mantenimiento': habitaciones.filter(estado='mantenimiento').count(),
        'reservas_activas': Reserva.objects.filter(activa=True, habitacion__hotel=hotel).count(),
    }
    return render(request, 'hotel/dashboard.html', context)


@login_required
def perfil_hotel(request):
    usuario = request.user
    
    if request.method == 'POST':
        # Guardar los cambios - esto funciona para admin y recepcionista
        usuario.first_name = request.POST.get('first_name', '')
        usuario.last_name = request.POST.get('last_name', '')
        usuario.email = request.POST.get('email', '')
        
        if hasattr(usuario, 'telefono'):
            usuario.telefono = request.POST.get('telefono', '')
        
        usuario.save()
        messages.success(request, 'Perfil actualizado correctamente')
        return redirect('perfil_hotel')
    
    # Obtener el hotel según el rol
    hotel = None
    if usuario.rol == 'recep':
        # Recepcionista: mostrar el hotel donde trabaja
        if hasattr(usuario, 'hotel'):
            hotel = usuario.hotel
        elif hasattr(usuario, 'hotel_set'):
            hotel = usuario.hotel_set.first()
    else:
        # Admin: podría no tener hotel asignado directo
        # O podrías mostrar el primer hotel que administra
        if hasattr(usuario, 'hoteles_administrados'):
            hotel = usuario.hoteles_administrados.first()
    
    context = {
        'usuario': usuario,
        'nombre_usuario': usuario.username,
        'nombres': usuario.first_name or '',
        'apellidos': usuario.last_name or '',
        'email': usuario.email or '',
        'telefono': getattr(usuario, 'telefono', ''),
        'hotel': hotel,
        'es_admin': usuario.rol == 'admin',
        'es_recepcionista': usuario.rol == 'recep',
    }
    
    return render(request, 'hotel/perfil.html', context)


@login_required
def gestionar_recepcionista(request, hotel_id):
    # Solo administradores pueden gestionar recepcionistas
    if request.user.rol != 'admin':
        messages.error(request, "⛔ Solo administradores pueden gestionar recepcionistas")
        return redirect('panel')  # ✅ Redirige al panel principal
    
    hotel = get_object_or_404(Hotel, id=hotel_id, usuario=request.user)
    
    # Buscar el recepcionista actual del hotel
    recepcionista_actual = Usuario.objects.filter(email=hotel.email, rol='recep').first()
    
    # Buscar recepcionistas disponibles (sin hotel asignado)
    hoteles_ids = Hotel.objects.exclude(email='').values_list('email', flat=True)
    recepcionistas_disponibles = Usuario.objects.filter(rol='recep').exclude(email__in=hoteles_ids).exclude(email='')
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        if accion == 'quitar':
            # Quitar recepcionista actual
            hotel.email = ''
            hotel.save()
            messages.success(request, f"✅ Recepcionista quitado del hotel {hotel.nombre}")
            return redirect('mis_hoteles')  # ✅ Este sí va a mis_hoteles porque es gestión
        
        elif accion == 'asignar':
            nuevo_email = request.POST.get('email')
            
            # Validar que el email no esté vacío
            if not nuevo_email:
                messages.error(request, "Debes seleccionar un recepcionista")
                return redirect('gestionar_recepcionista', hotel_id=hotel.id)
            
            nuevo_recep = get_object_or_404(Usuario, email=nuevo_email, rol='recep')
            
            # Verificar que no esté en otro hotel
            if Hotel.objects.filter(email=nuevo_email).exists():
                # Si está en otro hotel, lo quitamos de ahí primero
                otro_hotel = Hotel.objects.get(email=nuevo_email)
                otro_hotel.email = ''
                otro_hotel.save()
            
            # Asignar al hotel actual
            hotel.email = nuevo_email
            hotel.save()
            messages.success(request, f"✅ Recepcionista {nuevo_recep.username} asignado a {hotel.nombre}")
            return redirect('mis_hoteles')  # ✅ Redirige a mis_hoteles
    
    return render(request, 'hotel/gestionar_recepcionista.html', {
        'hotel': hotel,
        'recepcionista_actual': recepcionista_actual,
        'recepcionistas_disponibles': recepcionistas_disponibles
    })


@login_required
def agregar_recepcionista(request, hotel_id):
    # Solo administradores pueden agregar recepcionistas
    if request.user.rol != 'admin':
        messages.error(request, "⛔ Solo administradores pueden agregar recepcionistas")
        return redirect('panel')  # ✅ Redirige al panel principal
    
    hotel = get_object_or_404(Hotel, id=hotel_id, usuario=request.user)
    
    if request.method == 'POST':
        email = request.POST.get('email')
        nombre = request.POST.get('nombre', '')
        
        if not email:
            messages.error(request, "El email es obligatorio")
            return redirect('agregar_recepcionista', hotel_id=hotel.id)
        
        # Validar que el email no esté en uso
        if Usuario.objects.filter(email=email).exists():
            messages.error(request, f"❌ El email '{email}' ya está siendo usado por otro usuario")
            return redirect('agregar_recepcionista', hotel_id=hotel.id)
        
        # Validar que no sea el email del admin
        if email == request.user.email:
            messages.error(request, "❌ No puedes usar tu propio correo como recepcionista")
            return redirect('agregar_recepcionista', hotel_id=hotel.id)
        
        # Crear recepcionista
        username = f"recep_{hotel.id}_{''.join(random.choices(string.ascii_lowercase, k=4))}"
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        
        recepcionista = Usuario.objects.create_user(
            username=username,
            email=email,
            password=password,
            rol='recep',
            first_name=nombre or f"Recepcionista {hotel.nombre}"
        )
        
        # Asignar al hotel actual
        hotel.email = email
        hotel.save()
        
        # Enviar credenciales por correo
        try:
            send_mail(
                f"Credenciales de acceso - {hotel.nombre}",
                f"""
                Hola {nombre or 'Recepcionista'},
                
                Se ha creado un usuario para ti en el hotel {hotel.nombre}.
                
                Usuario: {username}
                Contraseña: {password}
                
                Puedes iniciar sesión en: {settings.SITE_URL}/login/
                
                Saludos,
                Equipo ChekinPro
                """,
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
        except Exception as e:
            messages.warning(request, f"Recepcionista creado pero no se pudo enviar el correo: {str(e)}")
        
        messages.success(request, f"✅ Recepcionista {username} creado y asignado a {hotel.nombre}")
        return redirect('mis_hoteles')  # ✅ Redirige a mis_hoteles
    
    return render(request, 'hotel/agregar_recepcionista.html', {'hotel': hotel})


@login_required
def detalle_hotel(request, hotel_id):
    if request.user.rol != 'admin':
        messages.error(request, "No tienes permiso")
        return redirect('panel')  # ✅ Redirige al panel principal
    
    hotel = get_object_or_404(Hotel, id=hotel_id, usuario=request.user)
    
    # Buscar recepcionistas por email
    recepcionistas = Usuario.objects.filter(email=hotel.email, rol='recep')
    
    return render(request, 'hotel/detalle.html', {
        'hotel': hotel,
        'recepcionistas': recepcionistas
    })


@login_required
def panel_hotel(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)
    
    # Verificar que el admin sea dueño
    if request.user.rol == 'admin' and hotel.usuario != request.user:
        messages.error(request, "No tienes permiso")
        return redirect('panel')
    
    habitaciones = Habitacion.objects.filter(hotel=hotel)
    
    context = {
        'hotel': hotel,
        'total_habitaciones': habitaciones.count(),
        'libres': habitaciones.filter(estado='libre').count(),
        'ocupadas': habitaciones.filter(estado='ocupada').count(),
        'mantenimiento': habitaciones.filter(estado='mantenimiento').count(),
    }
    return render(request, 'hotel/panel_hotel.html', context)