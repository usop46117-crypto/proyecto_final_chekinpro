from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Huesped, Acompanante  # 👈 IMPORTAR AMBOS MODELOS
from reservas.models import Reserva
from hotel.models import Hotel

# Función auxiliar para obtener el hotel
def obtener_hotel(request):
    if request.user.rol == 'recep':
        return Hotel.objects.filter(email=request.user.email).first()
    else:
        return request.user.hotel if hasattr(request.user, 'hotel') else None

@login_required
def huespedes_lista(request):
    # Obtener el hotel_id de la URL (viene como ?hotel=1)
    hotel_id = request.GET.get('hotel')
    
    if not hotel_id:
        messages.error(request, "No se especificó el hotel")
        return redirect('mis_hoteles')
    
    # Obtener el hotel específico
    hotel = get_object_or_404(Hotel, id=hotel_id)
    
    # Verificar permisos (solo el dueño o su recepcionista)
    if request.user.rol == 'admin' and hotel.usuario != request.user:
        messages.error(request, "No tienes permiso para ver este hotel")
        return redirect('mis_hoteles')
    elif request.user.rol == 'recep' and hotel.email != request.user.email:
        messages.error(request, "No tienes permiso para ver este hotel")
        return redirect('panel')
    
    # Obtener huéspedes con reservas activas en ESTE hotel
    huespedes = Huesped.objects.filter(
        reservas__habitacion__hotel=hotel,
        reservas__activa=True
    ).distinct()
    
    context = {
        'huespedes': huespedes,
        'hotel': hotel,  # Pasamos el hotel al template
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
    
    # 👇 OBTENER LOS ACOMPAÑANTES
    acompanantes = Acompanante.objects.filter(huesped=huesped)

    return render(request, 'reservas/por_huesped.html', {
        'huesped': huesped,
        'reservas': reservas,
        'acompanantes': acompanantes  # 👈 PASAR LOS ACOMPAÑANTES AL TEMPLATE
    })

from django.urls import reverse

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

    # Procesar el formulario completo (huésped + acompañantes)
    if request.method == 'POST':
        # 1. Datos del huésped
        nombre = request.POST.get('nombre', '').strip()
        documento = request.POST.get('documento', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        correo = request.POST.get('correo', '').strip()
        tiene_vehiculo = request.POST.get('tiene_vehiculo') == 'on'
        placa = request.POST.get('placa', '').strip().upper() if tiene_vehiculo else ''

        if not nombre or not documento or not telefono:
            messages.error(request, "❌ Los campos nombre, documento y teléfono son obligatorios")
            # Volver a cargar el formulario con los datos actuales
            acompanantes = Acompanante.objects.filter(huesped=huesped)
            return render(request, 'huespedes/editar.html', {'huesped': huesped, 'acompanantes': acompanantes})

        # Actualizar huésped
        huesped.nombre = nombre
        huesped.documento = documento
        huesped.telefono = telefono
        huesped.correo = correo
        huesped.tiene_vehiculo = tiene_vehiculo
        huesped.placa = placa
        huesped.save()

        # 2. Procesar acompañantes
        # 2a. Eliminar acompañantes marcados para borrar
        eliminar_ids = request.POST.getlist('acompanante_eliminar')
        if eliminar_ids:
            Acompanante.objects.filter(id__in=eliminar_ids, huesped=huesped).delete()

        # 2b. Actualizar o crear acompañantes
        i = 0
        while True:
            nombre_key = f'acompanante_nombre_{i}'
            if nombre_key not in request.POST:
                break
            nombre_acomp = request.POST.get(nombre_key, '').strip()
            documento_acomp = request.POST.get(f'acompanante_documento_{i}', '').strip()
            acomp_id = request.POST.get(f'acompanante_id_{i}')

            if nombre_acomp:  # Solo si tiene nombre
                if acomp_id:
                    # Actualizar existente
                    try:
                        acomp = Acompanante.objects.get(id=acomp_id, huesped=huesped)
                        acomp.nombre = nombre_acomp
                        acomp.documento = documento_acomp
                        acomp.save()
                    except Acompanante.DoesNotExist:
                        pass
                else:
                    # Crear nuevo
                    Acompanante.objects.create(
                        huesped=huesped,
                        nombre=nombre_acomp,
                        documento=documento_acomp
                    )
            i += 1

        messages.success(request, f'✅ Huésped {huesped.nombre} actualizado correctamente')
        # Redirigir a la lista de huéspedes del mismo hotel
        return redirect(f'/huespedes/?hotel={hotel.id}')

    # GET: mostrar formulario con acompañantes existentes
    acompanantes = Acompanante.objects.filter(huesped=huesped)
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
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        documento = request.POST.get('documento', '')
        
        Acompanante.objects.create(
            huesped=huesped,
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
        # Intentar obtener el acompañante
        acompanante = get_object_or_404(Acompanante, id=id, huesped__hotel=hotel)
        huesped = acompanante.huesped
        nombre = acompanante.nombre
        
        # Eliminar acompañante
        acompanante.delete()
        
        # Actualizar el contador de acompañantes
        huesped.acompanantes = Acompanante.objects.filter(huesped=huesped).count()
        huesped.save()
        
        messages.success(request, f'🗑️ Acompañante {nombre} eliminado correctamente')
        return redirect('huespedes:por_huesped', id=huesped.id)
        
    except Exception as e:
        messages.error(request, "Error al eliminar el acompañante")
        # Redirigir a la lista de huéspedes si no podemos obtener el ID
        return redirect('huespedes:huespedes_lista')