from django.db import models
from usuarios.models import Usuario

class Hotel(models.Model):
    
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="hoteles" 
    )
    nombre = models.CharField(max_length=150)
    logo = models.ImageField(upload_to="logos/", blank=True, null=True)
    tiene_parqueadero = models.BooleanField(default=False)
    direccion = models.CharField(max_length=200, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre