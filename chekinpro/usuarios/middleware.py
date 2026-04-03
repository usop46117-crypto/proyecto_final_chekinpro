# usuarios/middleware.py
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

class SuspensionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verificar si el request tiene el atributo user
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Si el usuario no está activo (is_active=False), bloquear acceso
            if not request.user.is_active:
                # Permitir solo logout
                if request.path != reverse('logout'):
                    messages.error(request, 
                        "🚫 **Acceso denegado**\n\n"
                        "Tu cuenta ha sido suspendida por el administrador. "
                        "No puedes acceder al sistema hasta que sea reactivada."
                    )
                    return redirect('logout')
        return self.get_response(request)