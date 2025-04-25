function ejecutarDeteccion() {
  fetch("/iniciar-deteccion", {
    method: "POST",
  })
    .then((response) => response.json())
    .then((data) => {
      document.getElementById("estado").innerText = data.estado;
    })
    .catch((err) => {
      console.error("Error:", err);
      document.getElementById("estado").innerText = "Error al ejecutar.";
    });
}
