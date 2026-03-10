from django.urls import path
from . import views

app_name = 'huespedes'

urlpatterns = [
    path('', views.huespedes_lista, name='huespedes_lista'),
    path('detalle/<int:id>/', views.huesped_detalle, name='por_huesped'),
    path('editar/<int:id>/', views.huesped_editar, name='huesped_editar'),
    path('acompanante/agregar/<int:huesped_id>/', views.agregar_acompanante, name='agregar_acompanante'),
    path('acompanante/eliminar/<int:id>/', views.eliminar_acompanante, name='eliminar_acompanante'),
]