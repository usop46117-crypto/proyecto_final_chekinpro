from .models import Notificacion

def notificaciones(request):
    """Context processor para pasar notificaciones a todas las plantillas"""
    context = {
        'notificaciones_no_leidas': 0,
        'notificaciones_recientes': [],
    }
    
    # Solo para usuarios autenticados
    if request.user.is_authenticated:
        # Obtener hotel de la URL o sesión
        hotel_id = request.GET.get('hotel') or request.session.get('hotel_id')
        
        # SOLO para administradores
        if hotel_id and request.user.rol == 'admin':
            try:
                from hotel.models import Hotel
                hotel = Hotel.objects.get(id=hotel_id, usuario=request.user)
                
                # 👇 VERIFICAR QUE HAY NOTIFICACIONES
                print(f"Hotel encontrado: {hotel.nombre}")
                print(f"Buscando notificaciones para usuario {request.user.id} y hotel {hotel.id}")
                
                # Notificaciones NO leídas del hotel actual
                no_leidas = Notificacion.objects.filter(
                    usuario=request.user,
                    hotel=hotel,
                    leida=False
                )
                context['notificaciones_no_leidas'] = no_leidas.count()
                print(f"Notificaciones no leídas: {context['notificaciones_no_leidas']}")
                
                # Últimas 5 notificaciones del hotel actual (TODAS, no solo no leídas)
                context['notificaciones_recientes'] = Notificacion.objects.filter(
                    usuario=request.user,
                    hotel=hotel
                ).order_by('-fecha')[:5]
                print(f"Notificaciones recientes: {len(context['notificaciones_recientes'])}")
                
            except Hotel.DoesNotExist:
                print("Hotel no encontrado")
                pass
        else:
            print(f"No es admin o no hay hotel_id. Rol: {request.user.rol}, hotel_id: {hotel_id}")
    
    return context