/**
 * UI helper functions for the room reservation system
 */

// Mostrar mensaje en la interfaz
function mostrarMensaje(mensaje, tipo) {
    const contenedor = document.getElementById('mensajesSistema');
    
    // Crear elemento de alerta
    const alertaElement = document.createElement('div');
    alertaElement.className = `alert alert-${tipo} alert-dismissible fade show`;
    alertaElement.innerHTML = `
      ${mensaje}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Añadir al contenedor
    contenedor.appendChild(alertaElement);
    
    // Auto-eliminar después de 8 segundos
    setTimeout(function() {
      alertaElement.remove();
    }, 8000);
  }
  
  // Mostrar/ocultar indicador de carga
  function mostrarLoading(mostrar) {
    document.getElementById('loadingOverlay').style.display = mostrar ? 'block' : 'none';
  }
  
  // Mostrar detalles de una reserva en modal
  function mostrarDetallesReserva(evento) {
    try {
      // Guardar ID para posible eliminación
      window.reservaIdSeleccionada = evento.id;
      
      // Propiedades extendidas contienen todos los datos
      const reserva = evento.extendedProps;
      
      // Formatear fecha
      let fechaStr = 'Fecha no disponible';
      try {
        const opciones = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        
        // Obtener fecha del evento (más confiable)
        const eventDate = evento.start || new Date(reserva.FECHA);
        fechaStr = eventDate.toLocaleDateString('es-ES', opciones);
      } catch (e) {
        console.error('Error al formatear fecha:', e);
      }
      
      // Crear HTML para el detalle
      const html = `
        <div class="card mb-3" style="border-left: 5px solid ${evento.backgroundColor}">
          <div class="card-body">
            <h5 class="card-title">Sala ${reserva.SALA_SELECCIONADA}</h5>
            <p><strong>Fecha:</strong> ${fechaStr}</p>
            <p><strong>Horario:</strong> ${reserva.HORA_INICIAL} - ${reserva.HORA_FINAL}</p>
            <p><strong>Área:</strong> ${reserva.AREA}</p>
            <p><strong>Personas:</strong> ${reserva.PROMEDIO_DE_PERSONAS_EN_REUNION}</p>
            <p><small class="text-muted">ID: ${reserva.ID_REUNION}</small></p>
          </div>
        </div>
        <div class="alert alert-warning">
          <i class="bi bi-exclamation-triangle"></i> ¿Seguro que deseas eliminar esta reserva? Esta acción no se puede deshacer.
        </div>
      `;
      
      // Mostrar en el modal
      document.getElementById('detalleReservaBody').innerHTML = html;
      
      // Abrir modal
      const modal = new bootstrap.Modal(document.getElementById('detalleReservaModal'));
      modal.show();
    } catch (error) {
      console.error('Error al mostrar detalles:', error);
      mostrarMensaje('Error al mostrar detalles de la reserva', 'danger');
    }
  }