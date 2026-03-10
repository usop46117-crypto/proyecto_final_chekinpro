from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Notificacion
from hotel.models import Hotel

@login_required
def lista_notificaciones(request):
    """Lista todas las notificaciones del administrador"""
    hotel_id = request.GET.get('hotel')
    
    if not hotel_id:
        messages.error(request, "No se especificó el hotel")
        return redirect('panel')
    
    hotel = get_object_or_404(Hotel, id=hotel_id, usuario=request.user)
    
    notificaciones = Notificacion.objects.filter(
        usuario=request.user,
        hotel=hotel
    ).order_by('-fecha')
    
    no_leidas = notificaciones.filter(leida=False).count()
    
    context = {
        'notificaciones': notificaciones,
        'hotel': hotel,
        'no_leidas': no_leidas,
    }
    return render(request, 'notificaciones/lista.html', context)

@login_required
def marcar_leida(request, id):
    """Marca una notificación como leída"""
    notificacion = get_object_or_404(Notificacion, id=id, usuario=request.user)
    notificacion.leida = True
    notificacion.save()
    
    hotel_id = request.GET.get('hotel')
    return redirect(f'/notificaciones/?hotel={hotel_id}')

@login_required
def marcar_todas_leidas(request):
    """Marca todas las notificaciones del hotel como leídas"""
    hotel_id = request.GET.get('hotel')
    
    if not hotel_id:
        messages.error(request, "No se especificó el hotel")
        return redirect('panel')
    
    hotel = get_object_or_404(Hotel, id=hotel_id, usuario=request.user)
    
    # Marcar todas las no leídas como leídas
    Notificacion.objects.filter(
        usuario=request.user,
        hotel=hotel,
        leida=False
    ).update(leida=True)
    
    messages.success(request, "Todas las notificaciones han sido marcadas como leídas")
    return redirect(f'/notificaciones/?hotel={hotel_id}')