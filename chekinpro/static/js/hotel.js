function agregarHabitacion() {

    const contenedor = document.getElementById("contenedor-habitaciones")

    const div = document.createElement("div")
    div.classList.add("d-flex", "gap-2", "mb-2")

    div.innerHTML = `
        <input type="text" name="habitaciones" class="form-control" placeholder="Ej: 102">
        <button type="button" class="btn btn-danger" onclick="this.parentElement.remove()">X</button>
    `

    contenedor.appendChild(div)
}