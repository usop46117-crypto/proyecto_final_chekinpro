from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Huesped
from reservas.models import Reserva, Acompanante
from hotel.models import Hotel

def obtener_hotel(request):
    if request.user.rol == 'recep':
        return Hotel.objects.filter(email=request.user.email).first()
    else:
        return request.user.hotel if hasattr(request.user, 'hotel') else None

@login_required
def huespedes_lista(request):
    hotel_id = request.GET.get('hotel')
    if not hotel_id:
        messages.error(request, "No se especificó el hotel")
        return redirect('mis_hoteles')
    hotel = get_object_or_404(Hotel, id=hotel_id)
    if request.user.rol == 'admin' and hotel.usuario != request.user:
        messages.error(request, "No tienes permiso para ver este hotel")
        return redirect('mis_hoteles')
    elif request.user.rol == 'recep' and hotel.email != request.user.email:
        messages.error(request, "No tienes permiso para ver este hotel")
        return redirect('panel')
    huespedes = Huesped.objects.filter(
        reservas__habitacion__hotel=hotel,
        reservas__activa=True
    ).distinct()
    for huesped in huespedes:
        reserva_activa = huesped.reservas.filter(activa=True).first()
        if reserva_activa:
            huesped.num_acompanantes = reserva_activa.acompanantes_list.count()
            huesped.tipo_vehiculo_reserva = reserva_activa.tipo_vehiculo  # desde la reserva
            huesped.placa_reserva = reserva_activa.placa
        else:
            huesped.num_acompanantes = 0
            huesped.tipo_vehiculo_reserva = None
            huesped.placa_reserva = None
    context = {
        'huespedes': huespedes,
        'hotel': hotel,
    }
    return render(request, 'huespedes/lista.html', context)

@login_required
def huesped_detalle(request, id):
    hotel = obtener_hotel(request)
    if not hotel:
        messages.error(request, "No tienes un hotel asignado")
        return redirect('panel')
    huesped = get_object_or_404(Huesped, id=id, hotel=hotel)
    reservas = Reserva.objects.filter(huesped=huesped).order_by('-fecha_entrada')
    reserva_activa = reservas.filter(activa=True).first()
    acompanantes = Acompanante.objects.filter(reserva=reserva_activa) if reserva_activa else []
    return render(request, 'reservas/por_huesped.html', {
        'huesped': huesped,
        'reservas': reservas,
        'reserva_activa': reserva_activa,
        'acompanantes': acompanantes,
        'hotel': hotel,
        'tiene_reserva_activa': reserva_activa is not None
    })

@login_required
def huesped_editar(request, id):
    hotel = obtener_hotel(request)
    if request.user.rol != 'recep':
        messages.error(request, "⛔ Solo recepcionistas pueden editar huéspedes")
        if hotel:
            return redirect(f'/huespedes/?hotel={hotel.id}')
        return redirect('panel')
    if not hotel:
        messages.error(request, "No tienes un hotel asignado")
        return redirect('panel')
    huesped = get_object_or_404(Huesped, id=id, hotel=hotel)
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        documento = request.POST.get('documento', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        correo = request.POST.get('correo', '').strip()
        tiene_vehiculo = request.POST.get('tiene_vehiculo') == 'on'
        placa = request.POST.get('placa', '').strip().upper() if tiene_vehiculo else ''
        if not nombre or not documento or not telefono:
            messages.error(request, "❌ Los campos nombre, documento y teléfono son obligatorios")
            acompanantes = Acompanante.objects.filter(reserva__huesped=huesped).distinct()
            return render(request, 'huespedes/editar.html', {'huesped': huesped, 'acompanantes': acompanantes})
        huesped.nombre = nombre
        huesped.documento = documento
        huesped.telefono = telefono
        huesped.correo = correo
        huesped.tiene_vehiculo = tiene_vehiculo
        huesped.placa = placa
        huesped.save()
        # También actualizar la reserva activa con la placa y tipo_vehiculo si es necesario
        reserva_activa = huesped.reservas.filter(activa=True).first()
        if reserva_activa:
            tipo_vehiculo = request.POST.get('tipo_vehiculo', '').strip() if tiene_vehiculo else ''
            reserva_activa.tipo_vehiculo = tipo_vehiculo
            reserva_activa.placa = placa
            reserva_activa.save()
        # Procesar acompañantes
        if reserva_activa:
            eliminar_ids = request.POST.getlist('acompanante_eliminar')
            if eliminar_ids:
                Acompanante.objects.filter(id__in=eliminar_ids, reserva=reserva_activa).delete()
            i = 0
            while True:
                nombre_key = f'acompanante_nombre_{i}'
                if nombre_key not in request.POST:
                    break
                nombre_acomp = request.POST.get(nombre_key, '').strip()
                documento_acomp = request.POST.get(f'acompanante_documento_{i}', '').strip()
                acomp_id = request.POST.get(f'acompanante_id_{i}')
                if nombre_acomp:
                    if acomp_id:
                        try:
                            acomp = Acompanante.objects.get(id=acomp_id, reserva=reserva_activa)
                            acomp.nombre = nombre_acomp
                            acomp.documento = documento_acomp
                            acomp.save()
                        except Acompanante.DoesNotExist:
                            pass
                    else:
                        Acompanante.objects.create(
                            reserva=reserva_activa,
                            nombre=nombre_acomp,
                            documento=documento_acomp
                        )
                i += 1
        messages.success(request, f'✅ Huésped {huesped.nombre} actualizado correctamente')
        return redirect(f'/huespedes/?hotel={hotel.id}')
    acompanantes = Acompanante.objects.filter(reserva__huesped=huesped).distinct() if huesped.reservas.exists() else []
    return render(request, 'huespedes/editar.html', {
        'huesped': huesped,
        'acompanantes': acompanantes
    })

    
@login_required
def agregar_acompanante(request, huesped_id):
    hotel = obtener_hotel(request)
    if not hotel:
        messages.error(request, "No tienes un hotel asignado")
        return redirect('panel')
    huesped = get_object_or_404(Huesped, id=huesped_id, hotel=hotel)
    reserva_activa = huesped.reservas.filter(activa=True).first()
    if not reserva_activa:
        messages.error(request, "No hay reserva activa para agregar acompañantes")
        return redirect('huespedes:por_huesped', id=huesped.id)
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        documento = request.POST.get('documento', '')
        Acompanante.objects.create(
            reserva=reserva_activa,
            nombre=nombre,
            documento=documento
        )
        messages.success(request, f'✅ Acompañante {nombre} agregado correctamente')
        return redirect('huespedes:por_huesped', id=huesped.id)
    return render(request, 'huespedes/agregar_acompanante.html', {'huesped': huesped})

@login_required
def eliminar_acompanante(request, id):
    hotel = obtener_hotel(request)
    if not hotel:
        messages.error(request, "No tienes un hotel asignado")
        return redirect('panel')
    try:
        acompanante = get_object_or_404(Acompanante, id=id, reserva__habitacion__hotel=hotel)
        huesped = acompanante.reserva.huesped
        nombre = acompanante.nombre
        acompanante.delete()
        messages.success(request, f'🗑️ Acompañante {nombre} eliminado correctamente')
        return redirect('huespedes:por_huesped', id=huesped.id)
    except Exception as e:
        messages.error(request, "Error al eliminar el acompañante")
        return redirect('huespedes:huespedes_lista')