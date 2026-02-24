# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Comandos de desarrollo

```bash
# Crear entorno virtual e instalar dependencias
python -m venv venv
pip install -r requirements.txt

# Ejecutar servidor en modo desarrollo (recarga automática)
uvicorn app.main:app --reload

# Ejecutar en producción (como Railway)
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

No hay suite de tests automatizados en este proyecto.

## Variables de entorno requeridas

Crear un archivo `.env` en la raíz del proyecto:

| Variable | Descripción | Por defecto |
|---|---|---|
| `DATABASE_URL` | Cadena de conexión PostgreSQL | `sqlite:///./dev.db` |
| `ENVIRONMENT` | `development` o `production` | `development` |
| `SECRET_KEY` | Clave para firmar cookies de sesión | valor inseguro por defecto |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | Credenciales admin | `admin` / `Chvs@2026#Admin!` |
| `MAIL_ENABLED` | `true`/`false` para habilitar emails | `false` |
| `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN` | Credenciales OAuth2 Gmail API | — |
| `MAIL_FROM` | Dirección de envío de emails | — |

> El enlace de cancelación en el email se construye a partir de `request.base_url` automáticamente (no requiere variable de entorno).

En producción (`ENVIRONMENT=production`) se carga `.env.production`. La lógica está en `app/config.py`.

## Arquitectura

Esta es una aplicación **FastAPI** de reservas de salas de juntas para CHVS. Todo el código de la aplicación vive en `app/`.

### Capas

- **`app/main.py`** — Punto de entrada. Define todas las rutas HTTP (públicas y de admin), lógica de negocio inline, y el envío de emails de confirmación usando la **Gmail API con OAuth2** (no SMTP) como `BackgroundTask`.
- **`app/models.py`** — Modelos SQLAlchemy: `Room`, `Booking`, `AdminUser`. Las tablas se crean automáticamente en el evento `startup` de FastAPI, junto con el seed de las dos salas y el usuario admin.
- **`app/schemas.py`** — Schemas Pydantic para la API REST (`/api/bookings`, `/api/rooms`).
- **`app/auth.py`** — Autenticación del panel admin: hashing bcrypt con `passlib`, y cookies de sesión firmadas con `itsdangerous` (`URLSafeTimedSerializer`). La dependencia `get_current_admin` protege todas las rutas `/admin/*`.
- **`app/database/db.py`** — Setup de SQLAlchemy. Convierte `postgres://` → `postgresql://` (comportamiento de Railway) y percent-encodea usuario/contraseña para evitar errores con caracteres especiales.
- **`app/config.py`** — Carga el `.env` correcto según la variable `ENVIRONMENT`.

### Frontend

- **`app/templates/`** — Plantillas Jinja2. `index.html` es la vista pública con el calendario; las plantillas `admin_*` forman el panel de administración.
- **`app/static/js/calendar.js`** — Lógica del calendario con **FullCalendar v6** (cargado desde CDN). Consume los endpoints `/api/bookings` y `/api/rooms`.
- **`app/static/css/style.css`** — Estilos corporativos (verde esmeralda y blanco).

### Reglas de negocio

- Reservas permitidas de **7:00 AM a 5:00 PM** (validado en backend).
- No se permiten solapamientos por sala (query de overlap en `main.py`).
- Dos salas fijas: **Sala Amarilla** (cap. 12) y **Sala Morada** (cap. 8), creadas en seed.
- Cada reserva valida que `attendees <= room.capacity`.
- El envío de email se controla con `MAIL_ENABLED=true/false`.
- Al crear una reserva se genera un `cancel_token` (48 h de validez). El email incluye un enlace `GET/POST /cancelar/{token}` que permite al usuario eliminar su propia reserva sin autenticación.
- Las migraciones de columnas nuevas se ejecutan en el startup con `ALTER TABLE ... ADD COLUMN` dentro de try/except (seguro para re-ejecuciones).
- Paleta de colores corporativa: `#62B33E` (principal) / `#4d9030` (oscuro).

### Flujo de autenticación admin

1. `POST /admin/login` verifica credenciales contra `admin_users` en BD.
2. Crea token firmado con `itsdangerous` y lo guarda en cookie `admin_session` (HttpOnly, 8h).
3. `get_current_admin` (dependencia FastAPI) valida la cookie en cada ruta protegida; redirige a `/admin/login` si es inválida o expirada.
