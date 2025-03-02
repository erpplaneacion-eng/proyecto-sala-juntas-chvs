/**
 * Google Sheets Model
 * Maneja la conexión e interacción con Google Sheets API
 */

const { google } = require('googleapis');
const path = require('path');
require('dotenv').config();

// Configuración de la hoja de cálculo
const SPREADSHEET_ID = process.env.SPREADSHEET_ID || '1UHsc-1rnMdiJfM8uycz4JjMVrQ74n-UzjOS8fQ6UaBk';
const SHEET_NAME = process.env.SHEET_NAME || 'Reservas';

// Encabezados de las columnas
const HEADERS = [
  'ID_REUNION',
  'FECHA',
  'HORA_INICIAL',
  'HORA_FINAL',
  'AREA',
  'SALA_SELECCIONADA',
  'PROMEDIO_DE_PERSONAS_EN_REUNION'
];

/**
 * Obtener cliente autenticado para Google API
 */
async function getAuthClient() {
  try {
    const auth = new google.auth.GoogleAuth({
      keyFile: path.join(__dirname, '../config/credentials.json'),
      scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });
    
    return await auth.getClient();
  } catch (error) {
    console.error('Error en la autenticación con Google:', error);
    throw new Error(`Error en la autenticación con Google: ${error.message}`);
  }
}

/**
 * Obtener instancia de la API de Sheets
 */
async function getSheetsAPI() {
  try {
    const authClient = await getAuthClient();
    return google.sheets({ version: 'v4', auth: authClient });
  } catch (error) {
    console.error('Error al obtener API de Sheets:', error);
    throw error;
  }
}

/**
 * Obtener o crear la hoja de reservas
 */
async function getOrCreateReservationsSheet() {
  try {
    const sheets = await getSheetsAPI();
    
    // Verificar si la hoja existe
    const sheetInfo = await sheets.spreadsheets.get({
      spreadsheetId: SPREADSHEET_ID,
    });
    
    const sheetExists = sheetInfo.data.sheets.some(
      sheet => sheet.properties.title === SHEET_NAME
    );
    
    if (!sheetExists) {
      console.log(`Hoja "${SHEET_NAME}" no encontrada. Creando...`);
      
      // Crear nueva hoja
      await sheets.spreadsheets.batchUpdate({
        spreadsheetId: SPREADSHEET_ID,
        resource: {
          requests: [
            {
              addSheet: {
                properties: {
                  title: SHEET_NAME,
                }
              }
            }
          ]
        }
      });
      
      // Añadir encabezados
      await sheets.spreadsheets.values.update({
        spreadsheetId: SPREADSHEET_ID,
        range: `${SHEET_NAME}!A1:G1`,
        valueInputOption: 'RAW',
        resource: {
          values: [HEADERS]
        }
      });
      
      console.log(`Hoja "${SHEET_NAME}" creada con éxito.`);
    } else {
      console.log(`Hoja "${SHEET_NAME}" encontrada.`);
    }
    
    return SHEET_NAME;
  } catch (error) {
    console.error('Error al verificar/crear hoja:', error);
    throw error;
  }
}

/**
 * Obtener todas las reservas
 */
exports.getReservations = async () => {
  try {
    console.log('Obteniendo reservas de Google Sheets...');
    
    const sheets = await getSheetsAPI();
    const sheetName = await getOrCreateReservationsSheet();
    
    // Obtener datos
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId: SPREADSHEET_ID,
      range: `${sheetName}!A:G`,
    });
    
    const rows = response.data.values || [];
    
    // Si solo hay encabezados o está vacía
    if (rows.length <= 1) {
      console.log('No hay reservas existentes.');
      return [];
    }
    
    // Procesar datos y formatear para cliente
    const headers = rows[0];
    const reservations = [];
    
    for (let i = 1; i < rows.length; i++) {
      if (rows[i].length > 0 && rows[i][0]) { // Si tiene ID
        const reservation = {};
        
        for (let j = 0; j < headers.length; j++) {
          reservation[headers[j]] = rows[i][j] || '';
        }
        
        // Formatear para cliente
        reservations.push({
          ID_REUNION: reservation.ID_REUNION,
          FECHA: reservation.FECHA,
          HORA_INICIAL: reservation.HORA_INICIAL,
          HORA_FINAL: reservation.HORA_FINAL,
          AREA: reservation.AREA || '',
          SALA_SELECCIONADA: reservation.SALA_SELECCIONADA || '',
          PROMEDIO_DE_PERSONAS_EN_REUNION: parseInt(reservation.PROMEDIO_DE_PERSONAS_EN_REUNION || 1)
        });
      }
    }
    
    console.log(`Se obtuvieron ${reservations.length} reservas.`);
    return reservations;
  } catch (error) {
    console.error('Error al obtener reservas:', error);
    throw error;
  }
};

/**
 * Crear una nueva reserva
 */
exports.createReservation = async (reservationData) => {
  try {
    console.log('Creando nueva reserva:', reservationData);
    
    const sheets = await getSheetsAPI();
    const sheetName = await getOrCreateReservationsSheet();
    
    // Preparar datos para insertar
    const values = [
      [
        reservationData.id,
        reservationData.fecha,
        reservationData.horaInicial,
        reservationData.horaFinal,
        reservationData.area,
        reservationData.salaSeleccionada,
        reservationData.personasReunion
      ]
    ];
    
    // Insertar en la hoja
    await sheets.spreadsheets.values.append({
      spreadsheetId: SPREADSHEET_ID,
      range: `${sheetName}!A:G`,
      valueInputOption: 'RAW',
      resource: {
        values: values
      }
    });
    
    console.log('Reserva creada con éxito:', reservationData.id);
    return true;
  } catch (error) {
    console.error('Error al crear reserva:', error);
    throw error;
  }
};

/**
 * Eliminar una reserva por ID
 */
exports.deleteReservation = async (id) => {
  try {
    console.log('Eliminando reserva:', id);
    
    const sheets = await getSheetsAPI();
    const sheetName = await getOrCreateReservationsSheet();
    
    // Obtener datos actuales
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId: SPREADSHEET_ID,
      range: `${sheetName}!A:A`,
    });
    
    const ids = response.data.values || [];
    let rowToDelete = -1;
    
    // Encontrar la fila con el ID
    for (let i = 0; i < ids.length; i++) {
      if (ids[i][0] === id) {
        rowToDelete = i + 1; // +1 porque las filas empiezan en 1 en Sheets
        break;
      }
    }
    
    if (rowToDelete === -1) {
      console.warn(`No se encontró reserva con ID: ${id}`);
      return false;
    }
    
    // Obtener ID de la hoja (sheetId)
    const sheetsInfo = await sheets.spreadsheets.get({
      spreadsheetId: SPREADSHEET_ID,
    });
    
    const sheet = sheetsInfo.data.sheets.find(s => s.properties.title === sheetName);
    if (!sheet) {
      throw new Error(`No se encontró la hoja "${sheetName}"`);
    }
    
    const sheetId = sheet.properties.sheetId;
    
    // Eliminar la fila
    await sheets.spreadsheets.batchUpdate({
      spreadsheetId: SPREADSHEET_ID,
      resource: {
        requests: [
          {
            deleteDimension: {
              range: {
                sheetId: sheetId,
                dimension: 'ROWS',
                startIndex: rowToDelete - 1, // Ajustar a índice base 0
                endIndex: rowToDelete
              }
            }
          }
        ]
      }
    });
    
    console.log(`Reserva eliminada con éxito: ${id}`);
    return true;
  } catch (error) {
    console.error('Error al eliminar reserva:', error);
    throw error;
  }
};

/**
 * Verificar conflictos de horario
 */
exports.checkConflicts = async (fecha, horaInicial, horaFinal, sala) => {
  try {
    console.log(`Verificando conflictos: ${fecha}, ${horaInicial}-${horaFinal}, Sala ${sala}`);
    
    // Obtener todas las reservas
    const reservations = await exports.getReservations();
    
    // Verificar conflictos
    const conflicts = [];
    
    for (const reserva of reservations) {
      // Ignorar si no es la misma sala
      if (reserva.SALA_SELECCIONADA !== sala) {
        continue;
      }
      
      // Formatear fecha de la reserva para comparación
      const fechaReserva = reserva.FECHA.split('T')[0]; // Extraer solo la parte de fecha si es ISO
      const fechaNueva = fecha.split('T')[0]; // Asegurar formato consistente
      
      // Continuar solo si es el mismo día
      if (fechaReserva !== fechaNueva) {
        continue;
      }
      
      // Convertir horas a minutos para facilitar comparación
      const [horaInicialNum, minutoInicialNum] = horaInicial.split(':').map(Number);
      const [horaFinalNum, minutoFinalNum] = horaFinal.split(':').map(Number);
      const inicioNuevo = horaInicialNum * 60 + minutoInicialNum;
      const finNuevo = horaFinalNum * 60 + minutoFinalNum;
      
      const [horaInicialReserva, minutoInicialReserva] = reserva.HORA_INICIAL.split(':').map(Number);
      const [horaFinalReserva, minutoFinalReserva] = reserva.HORA_FINAL.split(':').map(Number);
      const inicioExistente = horaInicialReserva * 60 + minutoInicialReserva;
      const finExistente = horaFinalReserva * 60 + minutoFinalReserva;
      
      // Verificar si hay solapamiento
      if ((inicioNuevo >= inicioExistente && inicioNuevo < finExistente) || 
          (finNuevo > inicioExistente && finNuevo <= finExistente) || 
          (inicioNuevo <= inicioExistente && finNuevo >= finExistente)) {
        conflicts.push({
          id: reserva.ID_REUNION,
          area: reserva.AREA,
          horario: `${reserva.HORA_INICIAL} - ${reserva.HORA_FINAL}`
        });
      }
    }
    
    const hasConflicts = conflicts.length > 0;
    console.log(`Conflictos encontrados: ${hasConflicts ? conflicts.length : 'Ninguno'}`);
    
    return { 
      hasConflicts,
      conflicts
    };
  } catch (error) {
    console.error('Error al verificar conflictos:', error);
    throw error;
  }
};

// Función para probar la conexión (solo para depuración)
exports.testConnection = async () => {
  try {
    const sheets = await getSheetsAPI();
    const sheetName = await getOrCreateReservationsSheet();
    
    return {
      success: true,
      message: `Conectado exitosamente a la hoja "${sheetName}"`,
      spreadsheetId: SPREADSHEET_ID
    };
  } catch (error) {
    console.error('Error en test de conexión:', error);
    return {
      success: false,
      message: `Error al conectar: ${error.message}`,
      error: error.toString()
    };
  }
};