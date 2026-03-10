from django.urls import path
from . import views

app_name = 'habitaciones'

urlpatterns = [
    path('', views.lista_habitaciones, name='lista_habitaciones'),
    path('crear/', views.crear_habitacion, name='crear_habitacion'),
    path('editar/<int:id>/', views.editar_habitacion, name='editar_habitacion'),
    path('mantenimiento/<int:id>/', views.poner_mantenimiento, name='poner_mantenimiento'),
    path('quitar-mantenimiento/<int:id>/', views.quitar_mantenimiento, name='quitar_mantenimiento'),
    path('eliminar/<int:id>/', views.eliminar_habitacion, name='eliminar_habitacion'),
]