/**
 * Calendar functionality for the room reservation system
 */

// Variables globales para el calendario
let calendario;
let reservas = [];

// Inicializar el calendario
function inicializarCalendario() {
  try {
    const calendarEl = document.getElementById('calendario');
    
    calendario = new FullCalendar.Calendar(calendarEl, {
      initialView: 'dayGridMonth',
      headerToolbar: {
        left: 'prev,next today',
        center: 'title',
        right: 'dayGridMonth,timeGridWeek,timeGridDay'
      },
      locale: 'es',
      timeZone: 'local',
      selectable: true,
      selectMirror: true,
      navLinks: true,
      dayMaxEvents: true,
      businessHours: {
        daysOfWeek: [1, 2, 3, 4, 5],
        startTime: '08:00',
        endTime: '18:00',
      },
      eventTimeFormat: {
        hour: '2-digit',
        minute: '2-digit',
        meridiem: false
      },
      eventClick: function(info) {
        mostrarDetallesReserva(info.event);
      },
      select: function(info) {
        // Pre-llenar el formulario con la fecha seleccionada
        document.getElementById('fecha').value = info.startStr.split('T')[0];
      }
    });
    
    calendario.render();
    console.log('Calendario inicializado');
  } catch (error) {
    console.error('Error al inicializar calendario:', error);
    mostrarMensaje('Error al inicializar el calendario', 'danger');
  }
}

// Cargar reservas desde el API
async function cargarReservas() {
  console.log('Cargando reservas...');
  mostrarLoading(true);
  
  // Mostrar mensaje de carga al usuario
  mostrarMensaje('Cargando reservas...', 'info');
  
  try {
    const response = await fetch('/api/reservas');
    const result = await response.json();
    
    mostrarLoading(false);
    console.log('Resultado de cargar reservas:', result);
    
    if (result && result.success === true) {
      reservas = result.reservas || [];
      
      // Hacer log detallado de las reservas recibidas
      console.log(`Se recibieron ${reservas.length} reservas:`);
      if (reservas.length > 0) {
        console.log('Primera reserva:', reservas[0]);
      }
      
      actualizarCalendario();
      mostrarMensaje(`Se cargaron ${reservas.length} reservas`, 'success');
    } else {
      console.error('Error al cargar reservas:', result);
      const mensaje = result && result.message ? result.message : 'No se pudieron cargar las reservas';
      const sugerencia = result && result.suggestion ? ` (${result.suggestion})` : '';
      mostrarMensaje(`No se pudieron cargar las reservas: ${mensaje}${sugerencia}`, 'warning');
      
      // Intentar actualizar el calendario aunque sea con datos vacíos
      reservas = [];
      actualizarCalendario();
    }
  } catch (error) {
    mostrarLoading(false);
    console.error('Error al cargar reservas:', error);
    mostrarMensaje('Error al cargar las reservas: ' + error.toString(), 'danger');
    
    // Para depuración
    if (typeof error === 'object') {
      for (const key in error) {
        console.error(`- ${key}: ${error[key]}`);
      }
    }
  }
}

// Actualizar eventos en el calendario con mejor manejo de fechas
function actualizarCalendario() {
  try {
    // Limpiar eventos actuales
    calendario.removeAllEvents();
    
    // Si no hay reservas, terminar
    if (!reservas || reservas.length === 0) {
      console.log('No hay reservas para mostrar');
      return;
    }
    
    // Filtros
    const mostrarAmarilla = document.getElementById('filtroAmarilla').checked;
    const mostrarMorada = document.getElementById('filtroMorada').checked;
    
    console.log('Filtros aplicados:', { amarilla: mostrarAmarilla, morada: mostrarMorada });
    console.log('Procesando', reservas.length, 'reservas para el calendario');
    
    // Procesar cada reserva
    reservas.forEach(function(reserva) {
      try {
        // Aplicar filtros
        if ((reserva.SALA_SELECCIONADA === 'Amarilla' && !mostrarAmarilla) ||
            (reserva.SALA_SELECCIONADA === 'Morada' && !mostrarMorada)) {
          return;
        }
        
        // Preparar fechas con mejor manejo de errores
        let fechaInicio, fechaFin;
        
        // Crear fecha base segura
        let fechaBase;
        try {
          // Si es un string ISO
          if (typeof reserva.FECHA === 'string' && reserva.FECHA.includes('T')) {
            console.log('FECHA es un string ISO:', reserva.FECHA);
            fechaBase = new Date(reserva.FECHA);
            console.log('Fecha base creada desde ISO:', fechaBase);
          } 
          // Otros formatos
          else {
            console.log('FECHA es otro formato:', typeof reserva.FECHA, reserva.FECHA);
            // Intentar convertir de forma general
            fechaBase = new Date(String(reserva.FECHA));
            
            // Si es inválida, intentar extraer componentes
            if (isNaN(fechaBase.getTime())) {
              console.warn('Fecha inválida, intentando parseo manual');
              
              // Intentar varios formatos comunes
              const strFecha = String(reserva.FECHA);
              
              // Formato DD/MM/YYYY
              if (strFecha.match(/^\d{1,2}\/\d{1,2}\/\d{4}$/)) {
                const [dia, mes, anio] = strFecha.split('/').map(Number);
                fechaBase = new Date(anio, mes - 1, dia); // Meses en JS son 0-based
              }
              // Formato YYYY-MM-DD
              else if (strFecha.match(/^\d{4}-\d{2}-\d{2}$/)) {
                const [anio, mes, dia] = strFecha.split('-').map(Number);
                fechaBase = new Date(anio, mes - 1, dia);
              }
              // Si todo falla, usar fecha actual
              else {
                console.error('No se pudo interpretar la fecha:', strFecha);
                fechaBase = new Date();
              }
            }
          }
        } catch (e) {
          console.error('Error procesando fecha base:', e);
          fechaBase = new Date(); // Fallback a hoy
        }
        
        // Extraer horas y minutos de forma segura
        let horaInicial = 8, minutoInicial = 0;
        let horaFinal = 9, minutoFinal = 0;
        
        try {
          if (reserva.HORA_INICIAL && reserva.HORA_INICIAL.includes(':')) {
            [horaInicial, minutoInicial] = reserva.HORA_INICIAL.split(':').map(Number);
          } else {
            console.warn('Formato de hora inicial inválido:', reserva.HORA_INICIAL);
          }
          
          if (reserva.HORA_FINAL && reserva.HORA_FINAL.includes(':')) {
            [horaFinal, minutoFinal] = reserva.HORA_FINAL.split(':').map(Number);
          } else {
            console.warn('Formato de hora final inválido:', reserva.HORA_FINAL);
          }
        } catch (e) {
          console.error('Error al procesar horas:', e);
        }
        
        // Crear fechas completas
        fechaInicio = new Date(fechaBase);
        fechaInicio.setHours(horaInicial, minutoInicial, 0);
        
        fechaFin = new Date(fechaBase);
        fechaFin.setHours(horaFinal, minutoFinal, 0);
        
        // Color según sala
        const color = reserva.SALA_SELECCIONADA === 'Amarilla' ? '#f1c232' : '#9900ff';
        const colorClase = reserva.SALA_SELECCIONADA === 'Amarilla' ? 'sala-amarilla' : 'sala-morada';
        
        // Mostrar información de depuración
        console.log('Añadiendo evento al calendario:', {
          id: reserva.ID_REUNION,
          title: `${reserva.SALA_SELECCIONADA} - ${reserva.AREA}`,
          start: fechaInicio,
          end: fechaFin,
          color: color
        });
        
        // Añadir evento
        calendario.addEvent({
          id: reserva.ID_REUNION,
          title: `${reserva.SALA_SELECCIONADA} - ${reserva.AREA}`,
          start: fechaInicio,
          end: fechaFin,
          backgroundColor: color,
          borderColor: color,
          classNames: [colorClase], // Usar clase CSS
          extendedProps: reserva
        });
      } catch (e) {
        console.error('Error al procesar reserva:', e, reserva);
      }
    });
    
    console.log('Calendario actualizado con éxito');
  } catch (error) {
    console.error('Error al actualizar calendario:', error);
    mostrarMensaje('Error al actualizar el calendario', 'danger');
  }
}

// Aplicar filtros al calendario
function aplicarFiltros() {
  actualizarCalendario();
  mostrarMensaje('Filtros aplicados', 'info');
}
