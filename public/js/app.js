/**
 * Main application logic for the room reservation system
 */

// Variables globales
window.reservaIdSeleccionada = null;

// Cuando el documento esté listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('Inicializando aplicación...');
    
    // Inicializar calendario
    inicializarCalendario();
    
    // Configurar eventos de botones
    document.getElementById('btnReservar').addEventListener('click', manejarReserva);
    document.getElementById('btnFiltrar').addEventListener('click', aplicarFiltros);
    
    // Configurar botón eliminar con log para depuración
    const btnEliminar = document.getElementById('btnEliminarReserva');
    console.log('Botón eliminar encontrado:', btnEliminar);
    btnEliminar.addEventListener('click', function() {
      console.log('Botón eliminar clickeado');
      eliminarReservaSeleccionada();
    });
    
    // Cargar reservas
    cargarReservas();
    
    // Mostrar mensaje de bienvenida
    mostrarMensaje('Sistema inicializado correctamente', 'info');
  });

// Manejar click en reservar
async function manejarReserva() {
  // Validación básica del formulario
  const salaSeleccionada = document.getElementById('salaSeleccionada').value;
  const fecha = document.getElementById('fecha').value;
  const horaInicial = document.getElementById('horaInicial').value;
  const horaFinal = document.getElementById('horaFinal').value;
  const area = document.getElementById('area').value;
  const personasReunion = document.getElementById('personasReunion').value;
  
  // Verificar campos obligatorios
  if (!salaSeleccionada || !fecha || !horaInicial || !horaFinal || !area) {
    mostrarMensaje('Por favor completa todos los campos requeridos', 'danger');
    return;
  }
  
  // Verificar horario
  if (horaInicial >= horaFinal) {
    mostrarMensaje('La hora final debe ser posterior a la hora inicial', 'warning');
    return;
  }
  
  // Preparar datos
  const reservaData = {
    salaSeleccionada: salaSeleccionada,
    fecha: fecha,
    horaInicial: horaInicial,
    horaFinal: horaFinal,
    area: area,
    personasReunion: parseInt(personasReunion) || 1
  };
  
  // Mostrar que estamos procesando
  mostrarMensaje('Procesando reserva...', 'info');
  mostrarLoading(true);
  
  // Imprimir datos para depuración
  console.log('Enviando datos de reserva:', JSON.stringify(reservaData));
  
  try {
    // Enviar al servidor
    const response = await fetch('/api/reservas', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(reservaData)
    });
    
    const result = await response.json();
    
    mostrarLoading(false);
    console.log('Respuesta del servidor:', result);
    
    if (result && result.success) {
      mostrarMensaje('✅ Reserva guardada con éxito', 'success');
      document.getElementById('formularioReserva').reset();
      cargarReservas(); // Recargar las reservas
    } else {
      const mensaje = result ? result.message : 'Error desconocido';
      mostrarMensaje('❌ Error: ' + mensaje, 'danger');
    }
  } catch (error) {
    mostrarLoading(false);
    console.error('Error en la solicitud:', error);
    mostrarMensaje('❌ Error en la comunicación con el servidor', 'danger');
  }
}

// Eliminar reserva seleccionada
async function eliminarReservaSeleccionada() {
    console.log('Función de eliminar ejecutada. ID seleccionado:', window.reservaIdSeleccionada);
    
    if (!window.reservaIdSeleccionada) {
      mostrarMensaje('No hay reserva seleccionada', 'warning');
      return;
    }
    
    mostrarLoading(true);
    console.log('Eliminando reserva:', window.reservaIdSeleccionada);
    
    try {
      const response = await fetch(`/api/reservas/${window.reservaIdSeleccionada}`, {
        method: 'DELETE'
      });
      
      const result = await response.json();
      
      mostrarLoading(false);
      
      // Cerrar el modal
      const modal = bootstrap.Modal.getInstance(document.getElementById('detalleReservaModal'));
      if (modal) modal.hide();
      
      if (result && result.success) {
        mostrarMensaje('Reserva eliminada con éxito', 'success');
        cargarReservas(); // Recargar reservas
      } else {
        mostrarMensaje('Error al eliminar: ' + (result ? result.message : 'Error desconocido'), 'danger');
      }
    } catch (error) {
      mostrarLoading(false);
      console.error('Error al eliminar:', error);
      mostrarMensaje('Error al comunicarse con el servidor', 'danger');
    }
    
    // Limpiar ID después de intentar eliminar
    window.reservaIdSeleccionada = null;
  }