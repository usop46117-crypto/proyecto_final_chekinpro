from django.urls import path
from . import views

app_name = 'reservas'

urlpatterns = [
    path('', views.lista_reservas, name='lista_reservas'),
    path('crear/', views.crear_reservas, name='crear_reservas'),
    path('historial/', views.historial, name='historial'), 
    path('detalle/<int:id>/', views.detalle_reserva, name='detalle_reserva'),
    path('huesped/<int:huesped_id>/', views.reservas_por_huesped, name='por_huesped'),
    path('checkout/<int:id>/', views.checkout_manual, name='checkout_manual'),  # Una sola vez
]