# GEMINI.md - Contexto del Proyecto: CHVS Sistema de Reserva de Salas

Este archivo proporciona contexto e instrucciones para el asistente de IA (Gemini) sobre la estructura, tecnologías y convenciones del proyecto de reserva de salas de la **Corporación Hacia un Valle Solidario (CHVS)**.

## 📌 Resumen del Proyecto
El sistema es una aplicación web para la gestión de reservas de dos salas de juntas específicas: **Sala Amarilla** (con Internet) y **Sala Morada**. Está diseñado para ser moderno, elegante (estilo Verde Esmeralda) y 100% responsivo.

- **Organización:** Corporación Hacia un Valle Solidario (CHVS).
- **Propósito:** Evitar conflictos de horarios y facilitar la reserva de espacios de reunión.

## 🛠️ Stack Tecnológico
- **Backend:** FastAPI (Python 3.x).
- **Base de Datos:** PostgreSQL con SQLAlchemy ORM.
- **Frontend:** 
    - **Templates:** Jinja2.
    - **Estilos:** Vanilla CSS (tema Emerald).
    - **Interactividad:** JavaScript (ES6+).
    - **Calendario:** FullCalendar v6.
- **Despliegue:** Railway.app.

## 📂 Estructura de Directorios Clave
- `app/main.py`: Punto de entrada de la aplicación, configuración de FastAPI y rutas de la API.
- `app/models.py`: Definición de los modelos de base de datos (`Room`, `Booking`).
- `app/schemas.py`: Esquemas Pydantic para validación de datos y serialización de la API.
- `app/database/db.py`: Configuración de la conexión a PostgreSQL y gestión de la sesión.
- `app/static/js/calendar.js`: Lógica del lado del cliente para el calendario y peticiones al backend.
- `app/templates/index.html`: Estructura principal de la interfaz de usuario.
- `requirements.txt`: Dependencias del proyecto.
- `Procfile` & `railway.json`: Configuración para el despliegue en Railway.

## ⚙️ Reglas de Negocio y Convenciones
- **Horario de Reserva:** Restringido entre las **7:00 AM y las 5:00 PM**.
- **Validación de Conflictos:** No se permiten reservas que se solapen en la misma sala.
- **Salas Predefinidas:** El sistema crea automáticamente las salas "Amarilla" y "Morada" en el primer inicio (`startup_db_seed`).
- **Estilo Visual:** Se debe mantener la identidad corporativa (Verde Esmeralda y Blanco).

## 🚀 Comandos de Desarrollo
- **Instalación:** `pip install -r requirements.txt`
- **Ejecución Local:** `uvicorn app.main:app --reload`
- **Variables de Entorno:** Configurar `DATABASE_URL` en un archivo `.env`.

## 📝 Notas para el Asistente
- Al modificar el frontend, asegúrate de mantener la responsividad (el calendario cambia de vista según el ancho de pantalla).
- Las validaciones de tiempo se realizan tanto en el frontend (vía `slotMinTime`/`slotMaxTime` en FullCalendar) como en el backend (en la ruta `POST /api/bookings`).
- El proyecto utiliza **Alembic** (o creación directa vía SQLAlchemy en `main.py`) para las tablas. Actualmente, `main.py` usa `Base.metadata.create_all`.
