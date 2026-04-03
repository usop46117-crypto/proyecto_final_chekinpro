from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    ROLES = (
        ('admin', 'Administrador'),
        ('recep', 'Recepcionista'),
    )
    
    rol = models.CharField(max_length=10, choices=ROLES, default='recep')
    profile_picture = models.ImageField(upload_to='perfiles/', blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)
    is_suspended = models.BooleanField(default=False) 
    
    def __str__(self):
        return f"{self.username} - {self.rol}"