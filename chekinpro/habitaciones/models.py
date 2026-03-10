from django.db import models
from hotel.models import Hotel

class Habitacion(models.Model):
    ESTADOS = (
        ("libre", "Libre"),
        ("ocupada", "Ocupada"),
        ("mantenimiento", "Mantenimiento"),
    )

    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.CASCADE,
        related_name="habitaciones"
    )
    numero = models.CharField(max_length=20)
    tipo = models.CharField(max_length=50)
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="libre"
    )

    class Meta:
        unique_together = ('hotel', 'numero')

    def __str__(self):
        return f"{self.numero} - {self.hotel.nombre}"