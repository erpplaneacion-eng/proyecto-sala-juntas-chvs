# GEMINI.md - Contexto del Proyecto: CHVS Sistema de Reserva de Salas

Este archivo proporciona contexto e instrucciones para el asistente de IA sobre la estructura, tecnologías y convenciones del proyecto de reserva de salas de la **Corporación Hacia un Valle Solidario (CHVS)**.

## 📌 Resumen del Proyecto
Sistema web para la gestión de reservas de dos salas de juntas: **Sala Amarilla** (con Internet, color `#FFD700`) y **Sala Morada** (color `#800080`). Diseñado con temática Verde Esmeralda, 100% responsivo, con calendario interactivo y panel de administración protegido.

- **Organización:** Corporación Hacia un Valle Solidario (CHVS).
- **Propósito:** Evitar conflictos de horarios y facilitar la reserva de espacios de reunión.
- **Despliegue:** Railway.app (producción).

## 🛠️ Stack Tecnológico
- **Backend:** FastAPI (Python 3.x) con Uvicorn.
- **Base de Datos:** PostgreSQL con SQLAlchemy ORM (creación de tablas vía `Base.metadata.create_all`).
- **Frontend:**
    - **Templates:** Jinja2 (5 plantillas HTML).
    - **Estilos:** Vanilla CSS (tema Emerald) en `app/static/css/style.css`.
    - **Interactividad:** JavaScript (ES6+) en `app/static/js/calendar.js`.
    - **Calendario:** FullCalendar v6.
- **Autenticación:** Cookies de sesión firmadas con `itsdangerous` + hash bcrypt con `passlib`.
- **Correo:** Gmail API (OAuth2) — **no usa SMTP saliente** (compatible con Railway).
- **Entornos:** `python-dotenv` con perfiles `development` (`.env`) y `production` (`.env.production`).

## 📂 Estructura de Directorios Clave
```
app/
├── main.py              # Punto de entrada, rutas públicas y de administración
├── models.py            # Modelos SQLAlchemy: Room, Booking, AdminUser
├── schemas.py           # Esquemas Pydantic para la API
├── auth.py              # Autenticación: bcrypt, cookies firmadas, get_current_admin()
├── config.py            # load_environment() — carga .env según ENVIRONMENT
├── credentials.json     # Credenciales OAuth2 para Gmail API
├── get_token.py         # Script auxiliar para obtener el refresh token de Gmail
├── database/
│   └── db.py            # Conexión PostgreSQL, Base, engine, get_db()
├── static/
│   ├── css/style.css    # Estilos globales (tema Emerald)
│   ├── js/calendar.js   # Lógica del calendario y peticiones al backend
│   └── img/             # Imágenes estáticas (imagen de fondo corporativa)
└── templates/
    ├── index.html           # Vista principal con FullCalendar
    ├── admin_login.html     # Login del administrador
    ├── admin_dashboard.html # Panel de administración con tabla de reservas y filtros
    ├── admin_edit_booking.html # Formulario crear/editar reserva (admin)
    └── email_booking.html   # Plantilla HTML del correo de confirmación
```
- `requirements.txt`: Dependencias del proyecto.
- `Procfile` & `railway.json`: Configuración para el despliegue en Railway.
- `test_email.py`: Script de prueba del envío de correo.

## 🗄️ Modelos de Base de Datos
| Modelo | Tabla | Campos principales |
|---|---|---|
| `Room` | `rooms` | `id`, `name`, `description`, `color` |
| `Booking` | `bookings` | `id`, `user_name`, `user_email`, `area`, `date`, `start_time`, `end_time`, `room_id`, `created_at` |
| `AdminUser` | `admin_users` | `id`, `username`, `hashed_password`, `is_active`, `created_at` |

## 🌐 Rutas de la API y Vistas
| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/` | Vista principal con el calendario |
| `GET` | `/api/bookings` | Lista todas las reservas (JSON) |
| `GET` | `/api/rooms` | Lista todas las salas (JSON) |
| `POST` | `/api/bookings` | Crea una reserva (público) |
| `GET` | `/admin/login` | Formulario de login |
| `POST` | `/admin/login` | Procesa el login, setea cookie de sesión (8h) |
| `GET` | `/admin/logout` | Cierra sesión y redirige a `/` |
| `GET` | `/admin` | Dashboard con tabla de reservas + filtros por sala y fecha |
| `GET/POST` | `/admin/bookings/new` | Crear reserva desde el admin |
| `GET/POST` | `/admin/bookings/{id}/edit` | Editar reserva existente |
| `POST` | `/admin/bookings/{id}/delete` | Eliminar reserva |

## ⚙️ Reglas de Negocio y Convenciones
- **Horario de Reserva:** Restringido entre las **7:00 AM y las 5:00 PM**. Validado en backend y frontend (FullCalendar `slotMinTime`/`slotMaxTime`).
- **Validación de Conflictos:** No se permiten reservas solapadas en la misma sala (validado en backend).
- **Salas Predefinidas:** Se crean automáticamente al inicio (`startup_db_seed`) si no existen.
- **Admin por defecto:** Se crea el usuario admin al inicio si no existe. Credenciales desde `ADMIN_USERNAME`/`ADMIN_PASSWORD` en las variables de entorno.
- **Correo de confirmación:** Se envía en segundo plano (`BackgroundTasks`) vía Gmail API al crear una reserva. Controlado por `MAIL_ENABLED=true/false`.
- **Estilo Visual:** Mantener la identidad corporativa (Verde Esmeralda y Blanco). La imagen de fondo está en `app/static/img/`.

## 🔑 Variables de Entorno Requeridas
| Variable | Descripción |
|---|---|
| `DATABASE_URL` | URL de conexión a PostgreSQL |
| `SECRET_KEY` | Clave para firmar las cookies de sesión |
| `ADMIN_USERNAME` | Nombre del usuario administrador |
| `ADMIN_PASSWORD` | Contraseña del administrador |
| `ENVIRONMENT` | `development` o `production` |
| `MAIL_ENABLED` | `true` / `false` — habilita envío de correos |
| `MAIL_FROM` | Dirección remitente del correo |
| `GMAIL_CLIENT_ID` | Client ID de la app OAuth2 de Google |
| `GMAIL_CLIENT_SECRET` | Client Secret de la app OAuth2 de Google |
| `GMAIL_REFRESH_TOKEN` | Refresh Token para la Gmail API |

## 🚀 Comandos de Desarrollo
- **Instalación:** `pip install -r requirements.txt`
- **Ejecución Local:** `uvicorn app.main:app --reload`
- **Archivos de entorno:** `.env` (desarrollo) y `.env.production` (producción).

## 📝 Notas para el Asistente
- **Responsividad:** El calendario cambia de vista según el ancho de pantalla. Preservar este comportamiento al modificar el frontend.
- **Autenticación Admin:** El sistema usa cookies firmadas (`itsdangerous`), no JWT. La sesión dura 8 horas.
- **Gmail API vs SMTP:** El proyecto usa OAuth2 con Gmail API para evitar restricciones de SMTP en Railway. No usar `smtplib` ni `aiosmtplib`.
- **Creación de tablas:** Se usa `Base.metadata.create_all` en el evento `startup`. No hay migraciones Alembic activas actualmente.
- **Formulario de reserva público:** Captura `user_name`, `user_email`, `area`, `booking_date`, `start_time`, `end_time`, `room_id`.
- **Perfiles de entorno:** `config.py` carga automáticamente `.env` o `.env.production` según la variable `ENVIRONMENT`.
