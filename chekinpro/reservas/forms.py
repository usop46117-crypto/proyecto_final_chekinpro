from django import forms
from .models import Reserva
from habitaciones.models import Habitacion
from huespedes.models import Huesped


class ReservaForm(forms.ModelForm):

    class Meta:
        model = Reserva
        fields = [
            'huesped',
            'habitacion',
            'fecha_entrada',
            'fecha_salida',
            'placa',
            'tipo_vehiculo',
        ]
        widgets = {
            'fecha_entrada': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_salida': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        hotel = kwargs.pop('hotel', None)
        super().__init__(*args, **kwargs)

        if hotel:
            # Solo huéspedes del hotel
            self.fields['huesped'].queryset = Huesped.objects.filter(hotel=hotel)

            # Solo habitaciones libres del hotel
            self.fields['habitacion'].queryset = Habitacion.objects.filter(
                hotel=hotel,
                estado="libre"
            )