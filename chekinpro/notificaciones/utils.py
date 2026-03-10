from .models import Notificacion

def crear_notificacion(usuario, hotel, accion, mensaje):
    """
    Crea una notificación para el administrador del hotel
    
    Args:
        usuario: El usuario admin que recibirá la notificación
        hotel: El hotel donde ocurrió la acción
        accion: Tipo de acción ('creacion', 'mantenimiento', 'disponible', 'eliminacion', 'reserva', 'checkout')
        mensaje: Mensaje descriptivo
    """
    
    # Mapeo de acciones a tipos (para el campo 'tipo' del modelo)
    tipos = {
        'creacion': 'reserva',      # 'reserva' existe en TIPOS
        'mantenimiento': 'acceso',   # 'acceso' existe en TIPOS
        'disponible': 'acceso',      # 'acceso' existe en TIPOS
        'eliminacion': 'acceso',     # 'acceso' existe en TIPOS
        'reserva': 'reserva',        # 'reserva' existe en TIPOS
        'checkout': 'checkout',      # 'checkout' existe en TIPOS
    }
    
    tipo_notificacion = tipos.get(accion, 'acceso')
    
    # Crear la notificación con los campos que tiene el modelo
    Notificacion.objects.create(
        usuario=usuario,
        hotel=hotel,
        tipo=tipo_notificacion,  # Usar el tipo mapeado
        mensaje=mensaje,
        leida=False
    )