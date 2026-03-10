from django.db import models
from usuarios.models import Usuario
from hotel.models import Hotel

class Notificacion(models.Model):
    TIPOS = (
        ('acceso', 'Acceso de recepcionista'),
        ('reserva', 'Nueva reserva'),
        ('checkout', 'Check-out realizado'),
    )
    
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones')
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='notificaciones')
    tipo = models.CharField(max_length=20, choices=TIPOS)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo} - {self.hotel.nombre}"