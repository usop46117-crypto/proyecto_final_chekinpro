from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from .models import Reserva, Acompanante
from habitaciones.models import Habitacion
from huespedes.models import Huesped
from hotel.models import Hotel
from notificaciones.utils import crear_notificacion
import re

def obtener_hotel(request):
    """Función auxiliar para obtener el hotel según el rol"""
    if request.user.rol == 'recep':
        return Hotel.objects.filter(email=request.user.email).first()
    elif request.user.rol == 'admin':
        hotel_id = request.GET.get('hotel') or request.session.get('hotel_id')
        if hotel_id:
            return get_object_or_404(Hotel, id=hotel_id, usuario=request.user)
    return None

@login_required
def lista_reservas(request):
    """Lista de reservas activas"""
    hotel = obtener_hotel(request)
    if not hotel:
        messages.error(request, "No tienes un hotel asignado")
        return redirect('panel')
    reservas = Reserva.objects.filter(
        activa=True,
        habitacion__hotel=hotel
    ).select_related('habitacion', 'huesped').order_by('-fecha_entrada')
    return render(request, "reservas/listar.html", {"reservas": reservas, "hotel": hotel})

@login_required
def historial(request):
    """Vista para ver SOLO las reservas finalizadas"""
    hotel_id = request.GET.get('hotel')
    if not hotel_id:
        messages.error(request, "No se especificó el hotel")
        return redirect('panel')
    hotel = get_object_or_404(Hotel, id=hotel_id)
    if request.user.rol == 'admin':
        if hotel.usuario != request.user:
            messages.error(request, "No tienes permiso para ver este hotel")
            return redirect('panel')
    elif request.user.rol == 'recep':
        hotel_recep = Hotel.objects.filter(email=request.user.email).first()
        if not hotel_recep or hotel_recep.id != hotel.id:
            messages.error(request, "No trabajas en este hotel")
            return redirect('panel')
    else:
        messages.error(request, "Rol no válido")
        return redirect('home')
    reservas = Reserva.objects.filter(
        habitacion__hotel=hotel,
        activa=False
    ).select_related('habitacion', 'huesped').order_by('-fecha_entrada')
    context = {
        'reservas': reservas,
        'hotel': hotel,
        'es_recepcionista': request.user.rol == 'recep',
        'es_administrador': request.user.rol == 'admin',
    }
    return render(request, 'reservas/historial.html', context)

@login_required
def crear_reservas(request):
    if request.user.rol != 'recep':
        messages.error(request, "⛔ Solo los recepcionistas pueden crear reservas")
        return redirect('panel')
    hotel = Hotel.objects.filter(email=request.user.email).first()
    if not hotel:
        messages.error(request, "No tienes un hotel asignado")
        return redirect('panel')
    habitaciones = Habitacion.objects.filter(hotel=hotel, estado='libre')
    if request.method == "POST":
        errores = []
        nombre = request.POST.get('nombre', '').strip()
        if not nombre:
            errores.append("El nombre del huésped es obligatorio")
        elif len(nombre) < 3:
            errores.append("El nombre debe tener al menos 3 caracteres")
        cedula = request.POST.get('cedula', '').strip()
        if not cedula:
            errores.append("El documento es obligatorio")
        elif len(cedula) < 5:
            errores.append("El documento debe tener al menos 5 caracteres")
        elif not cedula.isdigit():
            errores.append("El documento debe contener solo números")
        telefono = request.POST.get('telefono', '').strip()
        if not telefono:
            errores.append("El teléfono es obligatorio")
        else:
            telefono_limpio = re.sub(r'[\s\+\-]', '', telefono)
            if not telefono_limpio.isdigit():
                errores.append("El teléfono solo puede contener números, espacios, + y -")
            elif len(telefono_limpio) < 7:
                errores.append("El teléfono debe tener al menos 7 dígitos")
        correo = request.POST.get('correo', '').strip()
        if not correo:
            errores.append("El correo electrónico es obligatorio")
        habitacion_id = request.POST.get('habitacion')
        if not habitacion_id:
            errores.append("Debes seleccionar una habitación")
        else:
            try:
                habitacion = Habitacion.objects.get(id=habitacion_id, hotel=hotel)
                if habitacion.estado != 'libre':
                    errores.append(f"La habitación {habitacion.numero} no está disponible")
            except Habitacion.DoesNotExist:
                errores.append("La habitación seleccionada no existe")
        fecha_entrada = request.POST.get('fecha_entrada')
        fecha_salida = request.POST.get('fecha_salida')
        if not fecha_entrada or not fecha_salida:
            errores.append("Las fechas de entrada y salida son obligatorias")
        else:
            try:
                entrada = datetime.strptime(fecha_entrada, '%Y-%m-%d').date()
                salida = datetime.strptime(fecha_salida, '%Y-%m-%d').date()
                hoy = timezone.now().date()
                if entrada < hoy:
                    errores.append("La fecha de entrada no puede ser anterior a hoy")
                if salida <= entrada:
                    errores.append("La fecha de salida debe ser posterior a la entrada")
            except ValueError:
                errores.append("Formato de fecha inválido")
        tiene_vehiculo = request.POST.get('tiene_vehiculo') == 'on'
        tipo_vehiculo = request.POST.get('tipo_vehiculo', '').strip()
        placa = request.POST.get('placa', '').strip().upper()
        if tiene_vehiculo:
            if not tipo_vehiculo:
                errores.append("Debes seleccionar el tipo de vehículo")
            if not placa:
                errores.append("Debes ingresar la placa del vehículo")
            elif len(placa) < 3 or len(placa) > 10:
                errores.append("La placa debe tener entre 3 y 10 caracteres")
        huesped_existente = Huesped.objects.filter(
            documento=cedula,
            hotel=hotel
        ).first()
        if huesped_existente:
            reservas_activas = Reserva.objects.filter(
                huesped=huesped_existente,
                activa=True
            ).exists()
            if reservas_activas:
                errores.append(f"❌ El huésped con documento {cedula} ya tiene una reserva ACTIVA en este hotel")
        if errores:
            for error in errores:
                messages.error(request, f"❌ {error}")
            return render(request, "reservas/crear.html", {
                "habitaciones": habitaciones,
                "hotel": hotel,
                "datos": request.POST
            })
        # Crear o actualizar huésped (sin tipo_vehiculo, solo tiene_vehiculo y placa)
        if huesped_existente:
            huesped = huesped_existente
            huesped.nombre = nombre
            huesped.telefono = telefono
            huesped.correo = correo
            huesped.tiene_vehiculo = tiene_vehiculo
            huesped.placa = placa if tiene_vehiculo else None
            huesped.save()
            messages.info(request, f"ℹ️ Datos actualizados del huésped {huesped.nombre}")
        else:
            huesped = Huesped.objects.create(
                hotel=hotel,
                documento=cedula,
                nombre=nombre,
                telefono=telefono,
                correo=correo,
                tiene_vehiculo=tiene_vehiculo,
                placa=placa if tiene_vehiculo else None
            )
        reserva = Reserva.objects.create(
            habitacion=habitacion,
            huesped=huesped,
            fecha_entrada=entrada,
            fecha_salida=salida,
            activa=True,
            tipo_vehiculo=tipo_vehiculo if tiene_vehiculo else None,
            placa=placa if tiene_vehiculo else None
        )
        # Crear acompañantes vinculados a la reserva
        contador = 0
        while True:
            nombre_acomp = request.POST.get(f'acomp_nombre_{contador}', '').strip()
            if not nombre_acomp:
                break
            Acompanante.objects.create(
                reserva=reserva,
                nombre=nombre_acomp,
                documento=request.POST.get(f'acomp_documento_{contador}', '').strip() or None,
            )
            contador += 1
        habitacion.estado = 'ocupada'
        habitacion.save()
        try:
            admin = hotel.usuario
            crear_notificacion(
                usuario=admin,
                hotel=hotel,
                accion='reserva',
                mensaje=f"📅 El recepcionista {request.user.username} creó una reserva para {huesped.nombre} en habitación {habitacion.numero}"
            )
        except:
            pass
        messages.success(request, f"✅ Reserva creada para {huesped.nombre} en habitación {habitacion.numero}")
        return redirect(f'/huespedes/?hotel={hotel.id}')
    return render(request, "reservas/crear.html", {"habitaciones": habitaciones, "hotel": hotel})

@login_required
def checkout_manual(request, id):
    if request.user.rol != 'recep':
        messages.error(request, "⛔ Solo recepcionistas pueden hacer checkout")
        return redirect('panel')
    hotel = Hotel.objects.filter(email=request.user.email).first()
    if not hotel:
        messages.error(request, "No tienes un hotel asignado")
        return redirect('panel')
    try:
        reserva = Reserva.objects.get(id=id, habitacion__hotel=hotel)
    except Reserva.DoesNotExist:
        messages.error(request, "❌ La reserva no existe o no pertenece a tu hotel")
        return redirect('reservas:historial')
    if not reserva.activa:
        messages.warning(request, f"⚠️ Esta reserva ya está finalizada")
        return redirect('reservas:historial')
    nombre_huesped = reserva.huesped.nombre
    num_habitacion = reserva.habitacion.numero
    reserva.activa = False
    reserva.save()
    habitacion = reserva.habitacion
    habitacion.estado = 'libre'
    habitacion.save()
    try:
        admin = hotel.usuario
        crear_notificacion(
            usuario=admin,
            hotel=hotel,
            accion='checkout',
            mensaje=f"✅ Check-out realizado: {nombre_huesped} - Hab {num_habitacion} por {request.user.username}"
        )
    except:
        pass
    messages.success(request, f"✅ Check-out completado para {nombre_huesped} (Hab {num_habitacion})")
    return redirect(f'/reservas/historial/?hotel={hotel.id}')

@login_required
def reservas_por_huesped(request, huesped_id):
    hotel = obtener_hotel(request)
    if not hotel:
        messages.error(request, "No tienes un hotel asignado")
        return redirect('panel')
    try:
        huesped = Huesped.objects.get(id=huesped_id)
    except Huesped.DoesNotExist:
        messages.error(request, "El huésped no existe")
        return redirect('huespedes:lista')
    reservas = Reserva.objects.filter(huesped=huesped, habitacion__hotel=hotel).order_by('-fecha_entrada')
    if not reservas.exists():
        messages.warning(request, "Este huésped no tiene reservas en tu hotel")
        return redirect('huespedes:lista')
    reserva_activa = reservas.filter(activa=True).first()
    acompanantes = Acompanante.objects.filter(reserva=reserva_activa) if reserva_activa else []
    return render(request, 'reservas/por_huesped.html', {
        'huesped': huesped,
        'reserva_activa': reserva_activa,
        'reservas': reservas,
        'acompanantes': acompanantes,
        'hotel': hotel,
        'tiene_reserva_activa': reserva_activa is not None
    })

@login_required
def detalle_reserva(request, id):
    if request.user.rol == 'recep':
        hotel = Hotel.objects.filter(email=request.user.email).first()
        if not hotel:
            messages.error(request, "No tienes un hotel asignado")
            return redirect('panel')
        reserva = get_object_or_404(Reserva, id=id, habitacion__hotel=hotel)
    elif request.user.rol == 'admin':
        hoteles_admin = Hotel.objects.filter(usuario=request.user)
        reserva = get_object_or_404(Reserva, id=id, habitacion__hotel__in=hoteles_admin)
        hotel = reserva.habitacion.hotel
    else:
        messages.error(request, "Rol no válido")
        return redirect('home')
    acompanantes = Acompanante.objects.filter(reserva=reserva)
    return render(request, "reservas/detalle.html", {
        "reserva": reserva,
        "acompanantes": acompanantes,
        "hotel": hotel
    })