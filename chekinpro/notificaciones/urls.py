from django.urls import path
from . import views

app_name = 'notificaciones'

urlpatterns = [
    path('', views.lista_notificaciones, name='lista_notificaciones'),
    path('marcar/<int:id>/', views.marcar_leida, name='marcar_leida'),
    path('marcar-todas/', views.marcar_todas_leidas, name='marcar_todas_leidas'),  # 👈 ESTA ES LA QUE FALTA
]