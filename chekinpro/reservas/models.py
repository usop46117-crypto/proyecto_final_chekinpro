from django.db import models
from habitaciones.models import Habitacion
from huespedes.models import Huesped

class Reserva(models.Model):
    habitacion = models.ForeignKey(
        Habitacion,
        on_delete=models.CASCADE,
        related_name="reservas"
    )
    huesped = models.ForeignKey(
        Huesped,
        on_delete=models.CASCADE,
        related_name="reservas"
    )
    fecha_entrada = models.DateTimeField()
    fecha_salida = models.DateTimeField()
    placa = models.CharField(max_length=20, blank=True, null=True)
    tipo_vehiculo = models.CharField(max_length=50, blank=True, null=True)
    activa = models.BooleanField(default=True)
    creada = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        estado = "Activa" if self.activa else "Finalizada"
        return f"{self.huesped.nombre} - {self.habitacion.numero} - {estado}"

class Acompanante(models.Model):
    reserva = models.ForeignKey('Reserva', on_delete=models.CASCADE, related_name='acompanantes_list')
    nombre = models.CharField(max_length=100)
    documento = models.CharField(max_length=20, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    
    def __str__(self):
        return f"{self.nombre} - Reserva {self.reserva.id}"