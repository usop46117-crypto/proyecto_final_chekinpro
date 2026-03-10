const buscador = document.getElementById("buscador");
const tarjetas = document.querySelectorAll(".reserva-card");

buscador.addEventListener("keyup", function () {

    let texto = this.value.toLowerCase();

    tarjetas.forEach(function (card) {

        let huesped = card.dataset.huesped;
        let habitacion = card.dataset.habitacion;

        if (huesped.includes(texto) || habitacion.includes(texto)) {
            card.style.display = "block";
        } else {
            card.style.display = "none";
        }

    });

});