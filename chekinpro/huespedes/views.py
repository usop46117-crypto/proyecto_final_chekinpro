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
    # Primero obtener el hotel
    hotel = obtener_hotel(request)
    
    # Solo recepcionistas pueden editar huéspedes
    if request.user.rol != 'recep':
        messages.error(request, "⛔ Solo recepcionistas pueden editar huéspedes")
        if hotel:
            return redirect(f'/huespedes/?hotel={hotel.id}')  # 👈 URL DIRECTA
        return redirect('panel')
    
    if not hotel:
        messages.error(request, "No tienes un hotel asignado")
        return redirect('panel')

    huesped = get_object_or_404(Huesped, id=id, hotel=hotel)

    if request.method == 'POST':
        # Validar que los campos requeridos no estén vacíos
        nombre = request.POST.get('nombre', '').strip()
        documento = request.POST.get('documento', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        
        if not nombre or not documento or not telefono:
            messages.error(request, "❌ Los campos nombre, documento y teléfono son obligatorios")
            return render(request, 'huespedes/editar.html', {'huesped': huesped})
        
        huesped.nombre = nombre
        huesped.documento = documento
        huesped.telefono = telefono
        huesped.correo = request.POST.get('correo', '').strip()
        huesped.tiene_vehiculo = request.POST.get('tiene_vehiculo') == 'on'
        huesped.placa = request.POST.get('placa', '').strip().upper() if huesped.tiene_vehiculo else ''
        huesped.save()
        
        messages.success(request, f'✅ Huésped {huesped.nombre} actualizado correctamente')
        
        # 👈 SOLUCIÓN: URL DIRECTA (la que SÍ funciona)
        return redirect(f'/huespedes/?hotel={hotel.id}')

    return render(request, 'huespedes/editar.html', {'huesped': huesped})

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