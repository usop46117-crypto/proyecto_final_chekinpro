from django.db import models
from usuarios.models import Usuario
from hotel.models import Hotel

class Notificacion(models.Model):
    TIPOS = (
        ('creacion', 'Creación de habitación'),
        ('mantenimiento', 'Mantenimiento'),
        ('disponible', 'Habitación disponible'),
        ('eliminacion', 'Eliminación'),
        ('reserva', 'Nueva reserva'),
        ('checkout', 'Check-out'),
        ('exito', 'Éxito'),
        ('advertencia', 'Advertencia'),
        ('error', 'Error'),
        ('info', 'Información'),
        ('acceso', 'Acceso de recepcionista'),
    )
    
    usuario = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='notificaciones',
        null=True,   # Permitir nulo para notificaciones del sistema
        blank=True
    )
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='notificaciones')
    tipo = models.CharField(max_length=20, choices=TIPOS, default='info')
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.hotel.nombre}"