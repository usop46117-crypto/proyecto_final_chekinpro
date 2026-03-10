from django.db import models
from hotel.models import Hotel

class Huesped(models.Model):
    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.CASCADE,
        related_name='huespedes'
    )
    nombre = models.CharField(max_length=100)
    documento = models.CharField(max_length=50)
    correo = models.EmailField()
    telefono = models.CharField(max_length=20)
    
    # NUEVOS CAMPOS
    tiene_vehiculo = models.BooleanField(default=False)
    placa = models.CharField(max_length=10, blank=True, null=True)
    acompanantes = models.IntegerField(default=0)  # 👈 ESTE ES EL CAMPO ENTERO

    class Meta:
        unique_together = ('hotel', 'documento')

    def __str__(self):
        return f"{self.nombre} - {self.documento}"

class Acompanante(models.Model):
    huesped = models.ForeignKey(
        Huesped, 
        on_delete=models.CASCADE, 
        related_name='lista_acompanantes'  # 👈 CAMBIADO DE 'acompanantes' a 'lista_acompanantes'
    )
    nombre = models.CharField(max_length=100)
    documento = models.CharField(max_length=20, blank=True, null=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = 'Acompañante'
        verbose_name_plural = 'Acompañantes'