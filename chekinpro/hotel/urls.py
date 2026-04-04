from django.urls import path
from . import views
from django.contrib.auth import views as auth_views 

urlpatterns = [
    # Hoteles
    path('mis-hoteles/', views.mis_hoteles, name='mis_hoteles'),
    path('crear/', views.crear_hotel, name='crear_hotel'),
    path('panel/<int:hotel_id>/', views.panel_hotel, name='panel_hotel'),
    path('detalle/<int:hotel_id>/', views.detalle_hotel, name='detalle_hotel'),
    path('perfil/', views.perfil_hotel, name='perfil_hotel'),
    path('cambiar-contrasena/', auth_views.PasswordChangeView.as_view(
        template_name='registration/cambiar_contrasena.html',
        success_url='/hotel/perfil/?pass=exito'
    ), name='cambiar_contrasena'),
    
    
    # Recepcionistas
    path('gestionar-recepcionista/<int:hotel_id>/', views.gestionar_recepcionista, name='gestionar_recepcionista'),
    path('agregar-recepcionista/<int:hotel_id>/', views.agregar_recepcionista, name='agregar_recepcionista'),
    path('hotel/editar/<int:hotel_id>/', views.editar_hotel, name='editar_hotel'),

    #Perfiles
    path('perfil/subir-foto/', views.upload_profile_picture, name='upload_profile_picture'),
    
]