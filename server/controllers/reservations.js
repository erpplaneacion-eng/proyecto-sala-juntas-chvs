/**
 * Controlador de Reservas
 * Maneja la lógica de negocio para las operaciones de reservas
 */

const sheetModel = require('../models/sheet');
const { v4: uuidv4 } = require('uuid');

/**
 * Obtener todas las reservas
 */
exports.getAllReservations = async (req, res) => {
  try {
    console.log('Controlador: Obteniendo todas las reservas');
    
    const reservations = await sheetModel.getReservations();
    
    res.json({
      success: true,
      reservas: reservations
    });
  } catch (error) {
    console.error('Error al obtener reservas:', error);
    res.status(500).json({
      success: false,
      message: `Error al obtener reservas: ${error.message}`
    });
  }
};

/**
 * Crear una nueva reserva
 */
exports.createReservation = async (req, res) => {
  try {
    console.log('Controlador: Creando nueva reserva:', req.body);
    
    // Validación básica del formulario
    const { salaSeleccionada, fecha, horaInicial, horaFinal, area, personasReunion } = req.body;
    
    if (!salaSeleccionada || !fecha || !horaInicial || !horaFinal || !area) {
      return res.status(400).json({
        success: false,
        message: 'Faltan campos requeridos'
      });
    }
    
    // Verificar horario
    if (horaInicial >= horaFinal) {
      return res.status(400).json({
        success: false,
        message: 'La hora final debe ser posterior a la hora inicial'
      });
    }
    
    // Verificar conflictos de horario
    const { hasConflicts, conflicts } = await sheetModel.checkConflicts(
      fecha, 
      horaInicial, 
      horaFinal, 
      salaSeleccionada
    );
    
    if (hasConflicts) {
      return res.status(409).json({
        success: false,
        message: 'La sala ya está reservada en ese horario',
        conflictos: conflicts
      });
    }
    
    // Crear reserva
    const id = uuidv4();
    
    const reservationData = {
      id,
      fecha,
      horaInicial,
      horaFinal,
      area,
      salaSeleccionada,
      personasReunion: parseInt(personasReunion) || 1
    };
    
    const result = await sheetModel.createReservation(reservationData);
    
    res.status(201).json({
      success: true,
      message: 'Reserva guardada correctamente',
      id: id
    });
  } catch (error) {
    console.error('Error al crear reserva:', error);
    res.status(500).json({
      success: false,
      message: `Error al crear reserva: ${error.message}`
    });
  }
};

/**
 * Eliminar una reserva
 */
exports.deleteReservation = async (req, res) => {
    try {
      const id = req.params.id;
      
      console.log('API: Solicitud de eliminar reserva recibida con ID:', id);
      
      if (!id) {
        console.log('API: Error - ID de reserva no proporcionado');
        return res.status(400).json({
          success: false,
          message: 'ID de reserva no proporcionado'
        });
      }
      
      console.log('Controlador: Eliminando reserva con ID:', id);
      
      const result = await sheetModel.deleteReservation(id);
      
      if (!result) {
        console.log('API: Error - Reserva no encontrada');
        return res.status(404).json({
          success: false,
          message: 'Reserva no encontrada'
        });
      }
      
      console.log('API: Reserva eliminada con éxito');
      res.json({
        success: true,
        message: 'Reserva eliminada con éxito'
      });
    } catch (error) {
      console.error('Error al eliminar reserva:', error);
      res.status(500).json({
        success: false,
        message: `Error al eliminar reserva: ${error.message}`
      });
    }
  };