/**
 * Rutas API para el Sistema de Reserva de Salas
 */

const express = require('express');
const router = express.Router();
const reservationController = require('../controllers/reservations');

// Ruta de prueba
router.get('/test', (req, res) => {
  res.json({ message: 'API funcionando correctamente' });
});

// Ruta para probar la conexión a Google Sheets
router.get('/test-sheets', async (req, res) => {
  try {
    const sheetModel = require('../models/sheet');
    const result = await sheetModel.testConnection();
    res.json(result);
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message
    });
  }
});

// Rutas para reservas
router.get('/reservas', reservationController.getAllReservations);
router.post('/reservas', reservationController.createReservation);
router.delete('/reservas/:id', reservationController.deleteReservation);

module.exports = router;