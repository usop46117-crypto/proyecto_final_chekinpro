from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Habitacion
from hotel.models import Hotel
from reservas.models import Reserva
from notificaciones.utils import crear_notificacion
from django.core.paginator import Paginator 

@login_required
def lista_habitaciones(request):
    # Obtener el hotel de la URL
    hotel_id = request.GET.get('hotel')
    if not hotel_id:
        messages.error(request, 'No se especificó el hotel')
        return redirect('home')
    
    hotel = get_object_or_404(Hotel, id=hotel_id)
    
    # VERIFICACIÓN DE PERMISOS SEGÚN ROL
    if request.user.rol == 'admin':
        if hotel.usuario != request.user:
            messages.error(request, 'No tienes permiso para ver este hotel.')
            return redirect('home')
    elif request.user.rol == 'recep':
        hotel_recep = Hotel.objects.filter(email=request.user.email).first()
        if not hotel_recep or hotel_recep.id != hotel.id:
            messages.error(request, 'No trabajas en este hotel.')
            return redirect('panel')
    else:
        messages.error(request, 'Rol no válido')
        return redirect('home')
    
    # Obtener todas las habitaciones del hotel
    habitaciones_list = Habitacion.objects.filter(hotel=hotel)
    
    # ============================================
    # APLICAR FILTROS DE BÚSQUEDA
    # ============================================
    numero_filtro = request.GET.get('numero')
    estado_filtro = request.GET.get('estado')
    
    if numero_filtro:
        habitaciones_list = habitaciones_list.filter(numero__icontains=numero_filtro)
    
    if estado_filtro:
        habitaciones_list = habitaciones_list.filter(estado=estado_filtro)
    
    # Ordenar por número
    habitaciones_list = habitaciones_list.order_by('numero')
    
    # Paginación: 10 habitaciones por página
    paginator = Paginator(habitaciones_list, 10)
    page_number = request.GET.get('page')
    habitaciones = paginator.get_page(page_number)
    
    # Estadísticas (sobre todas las habitaciones, no solo las filtradas)
    todas_habitaciones = Habitacion.objects.filter(hotel=hotel)
    total_habitaciones = todas_habitaciones.count()
    libres = todas_habitaciones.filter(estado='libre').count()
    ocupadas = todas_habitaciones.filter(estado='ocupada').count()
    mantenimiento = todas_habitaciones.filter(estado='mantenimiento').count()
    
    context = {
        'hotel': hotel,
        'habitaciones': habitaciones,
        'total_habitaciones': total_habitaciones,
        'libres': libres,
        'ocupadas': ocupadas,
        'mantenimiento': mantenimiento,
        'es_recepcionista': request.user.rol == 'recep',
        'es_administrador': request.user.rol == 'admin',
    }
    return render(request, 'habitaciones/lista.html', context)

@login_required
def crear_habitacion(request):
    # Solo recepcionistas pueden crear habitaciones
    if request.user.rol != 'recep':
        messages.error(request, "⛔ Solo recepcionistas pueden crear habitaciones")
        return redirect('habitaciones:lista_habitaciones')
    
    # Obtener hotel del recepcionista
    hotel = Hotel.objects.filter(email=request.user.email).first()
    if not hotel:
        messages.error(request, "No tienes un hotel asignado")
        return redirect('panel')

    if request.method == 'POST':
        numero = request.POST.get('numero')
        tipo = request.POST.get('tipo')

        if Habitacion.objects.filter(hotel=hotel, numero=numero).exists():
            messages.error(request, f"❌ Ya existe una habitación con el número {numero}")
            return render(request, 'habitaciones/crear.html', {'hotel': hotel})

        if numero and tipo:
            Habitacion.objects.create(
                hotel=hotel,
                numero=numero,
                tipo=tipo,
                estado='libre'
            )
            
            # ============================================
            # NOTIFICACIÓN AL ADMIN - NUEVA HABITACIÓN
            # ============================================
            try:
                admin = hotel.usuario
                crear_notificacion(
                    usuario=admin,
                    hotel=hotel,
                    accion='reserva',
                    mensaje=f"🏨 El recepcionista {request.user.username} creó la habitación {numero} ({tipo})"
                )
            except:
                pass
            
            messages.success(request, f'✅ Habitación {numero} creada correctamente')
            return redirect(f'/habitaciones/?hotel={hotel.id}')

    return render(request, 'habitaciones/crear.html', {'hotel': hotel})

@login_required
def editar_habitacion(request, id):
    # Solo recepcionistas pueden editar habitaciones
    if request.user.rol != 'recep':
        messages.error(request, "⛔ Solo recepcionistas pueden editar habitaciones")
        return redirect('habitaciones:lista_habitaciones')
    
    # Obtener hotel del recepcionista
    hotel = Hotel.objects.filter(email=request.user.email).first()
    if not hotel:
        messages.error(request, "No tienes un hotel asignado")
        return redirect('panel')

    habitacion = get_object_or_404(Habitacion, id=id, hotel=hotel)

    if request.method == 'POST':
        numero = request.POST.get('numero')
        tipo = request.POST.get('tipo')

        # Verificar que no exista otra habitación con el mismo número
        if Habitacion.objects.filter(hotel=hotel, numero=numero).exclude(id=id).exists():
            messages.error(request, f"❌ Ya existe otra habitación con el número {numero}")
            return render(request, 'habitaciones/editar.html', {'habitacion': habitacion, 'hotel': hotel})

        if numero and tipo:
            habitacion.numero = numero
            habitacion.tipo = tipo
            habitacion.save()
            
            messages.success(request, f"✅ Habitación {numero} actualizada correctamente")
            return redirect(f'/habitaciones/?hotel={hotel.id}')

    return render(request, 'habitaciones/editar.html', {'habitacion': habitacion, 'hotel': hotel})

@login_required
def poner_mantenimiento(request, id):
    # Solo recepcionistas pueden cambiar estados
    if request.user.rol != 'recep':
        messages.error(request, "⛔ Solo recepcionistas pueden cambiar estados")
        return redirect('habitaciones:lista_habitaciones')
    
    # Obtener hotel del recepcionista
    hotel = Hotel.objects.filter(email=request.user.email).first()
    if not hotel:
        messages.error(request, "No tienes un hotel asignado")
        return redirect('panel')
    
    habitacion = get_object_or_404(Habitacion, id=id, hotel=hotel)
    
    # ❌ VERIFICAR SI LA HABITACIÓN ESTÁ OCUPADA
    if habitacion.estado == 'ocupada':
        messages.error(
            request, 
            f"❌ No se puede poner en mantenimiento la habitación {habitacion.numero} porque está OCUPADA. "
            f"Debes esperar a que hagan checkout primero."
        )
        return redirect(f'/habitaciones/?hotel={hotel.id}')
    
    # Si ya está en mantenimiento
    if habitacion.estado == 'mantenimiento':
        messages.warning(request, f"⚠️ La habitación {habitacion.numero} ya está en mantenimiento")
        return redirect(f'/habitaciones/?hotel={hotel.id}')
    
    # Cambiar a mantenimiento
    habitacion.estado = 'mantenimiento'
    habitacion.save()
    
    # ============================================
    # NOTIFICACIÓN AL ADMIN - MANTENIMIENTO
    # ============================================
    try:
        admin = hotel.usuario
        crear_notificacion(
            usuario=admin,
            hotel=hotel,
            accion='reserva',
            mensaje=f"🔧 El recepcionista {request.user.username} puso en mantenimiento la habitación {habitacion.numero}"
        )
    except:
        pass
    
    messages.success(request, f"✅ Habitación {habitacion.numero} puesta en mantenimiento")
    return redirect(f'/habitaciones/?hotel={hotel.id}')

@login_required
def quitar_mantenimiento(request, id):
    # Solo recepcionistas pueden cambiar estados
    if request.user.rol != 'recep':
        messages.error(request, "⛔ Solo recepcionistas pueden cambiar estados")
        return redirect('habitaciones:lista_habitaciones')
    
    # Obtener hotel del recepcionista
    hotel = Hotel.objects.filter(email=request.user.email).first()
    if not hotel:
        messages.error(request, "No tienes un hotel asignado")
        return redirect('panel')
    
    habitacion = get_object_or_404(Habitacion, id=id, hotel=hotel)
    
    # Verificar que está en mantenimiento
    if habitacion.estado != 'mantenimiento':
        messages.warning(request, f"⚠️ La habitación {habitacion.numero} no está en mantenimiento")
        return redirect(f'/habitaciones/?hotel={hotel.id}')
    
    habitacion.estado = 'libre'
    habitacion.save()
    
    # ============================================
    # NOTIFICACIÓN AL ADMIN - QUITAR MANTENIMIENTO
    # ============================================
    try:
        admin = hotel.usuario
        crear_notificacion(
            usuario=admin,
            hotel=hotel,
            accion='reserva',
            mensaje=f"✅ El recepcionista {request.user.username} quitó el mantenimiento de la habitación {habitacion.numero}"
        )
    except:
        pass
    
    messages.success(request, f"✅ Habitación {habitacion.numero} disponible nuevamente")
    return redirect(f'/habitaciones/?hotel={hotel.id}')

@login_required
def eliminar_habitacion(request, id):
    # Solo recepcionistas pueden eliminar habitaciones
    if request.user.rol != 'recep':
        messages.error(request, "⛔ Solo recepcionistas pueden eliminar habitaciones")
        return redirect('habitaciones:lista_habitaciones')
    
    # Obtener hotel del recepcionista
    hotel = Hotel.objects.filter(email=request.user.email).first()
    if not hotel:
        messages.error(request, "No tienes un hotel asignado")
        return redirect('panel')
    
    habitacion = get_object_or_404(Habitacion, id=id, hotel=hotel)

    # ❌ VERIFICAR SI TIENE RESERVAS ACTIVAS (usa 'activa' en lugar de 'estado')
    reservas_activas = Reserva.objects.filter(
        habitacion=habitacion,
        activa=True
    ).exists()
    
    if reservas_activas:
        messages.error(
            request, 
            f"❌ No se puede eliminar la habitación {habitacion.numero} porque tiene RESERVAS ACTIVAS. "
            f"Debes realizar el checkout de todas las reservas primero."
        )
        return redirect(f'/habitaciones/?hotel={hotel.id}')
    
    # ❌ VERIFICAR SI ESTÁ OCUPADA
    if habitacion.estado == 'ocupada':
        messages.error(
            request, 
            f"❌ No se puede eliminar la habitación {habitacion.numero} porque está OCUPADA."
        )
        return redirect(f'/habitaciones/?hotel={hotel.id}')
    
    # Verificar si tiene historial de reservas (solo para informar)
    tiene_historial = Reserva.objects.filter(habitacion=habitacion).exists()
    
    numero = habitacion.numero
    habitacion.delete()
    
    # ============================================
    # NOTIFICACIÓN AL ADMIN - ELIMINAR HABITACIÓN
    # ============================================
    try:
        admin = hotel.usuario
        crear_notificacion(
            usuario=admin,
            hotel=hotel,
            accion='reserva',
            mensaje=f"🗑️ El recepcionista {request.user.username} eliminó la habitación {numero}"
        )
    except:
        pass
    
    if tiene_historial:
        messages.success(request, f"✅ Habitación {numero} eliminada correctamente. Tenía historial de reservas.")
    else:
        messages.success(request, f"✅ Habitación {numero} eliminada correctamente.")
    
    return redirect(f'/habitaciones/?hotel={hotel.id}')