from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.registro, name='registro'),
    path('panel/', views.panel, name='panel'),
    path('saber-mas/', views.saber_mas, name='saber_mas'),
    path('perfil/', views.mi_perfil, name='mi_perfil'),

    path('recuperar/', views.recuperar_password, name='recuperar_password'),
    path('reset/<uidb64>/<token>/', views.reset_password_confirm, name='reset_password_confirm'),
]