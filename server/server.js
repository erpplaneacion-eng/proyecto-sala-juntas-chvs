/**
 * Server entry point for Room Reservation System
 */

// Cargar variables de entorno
require('dotenv').config();

// Importar dependencias
const express = require('express');
const path = require('path');
const cors = require('cors');

// Rutas API
const apiRoutes = require('./routes/api');

// Crear aplicación Express
const app = express();

// Puerto
const PORT = process.env.PORT || 3000;

// Middlewares
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: false }));

// Servir archivos estáticos
app.use(express.static(path.join(__dirname, '../public')));

// Rutas API
app.use('/api', apiRoutes);

// Ruta de captura para SPA
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../public/index.html'));
});

// Manejo de errores
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(err.status || 500).json({
    success: false,
    message: err.message || 'Error interno del servidor'
  });
});

// Iniciar servidor
app.listen(PORT, () => {
  console.log(`Servidor iniciado en el puerto ${PORT}`);
  console.log(`Ambiente: ${process.env.NODE_ENV || 'development'}`);
  console.log(`API disponible en: http://localhost:${PORT}/api/test`);
});