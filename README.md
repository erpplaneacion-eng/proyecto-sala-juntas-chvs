# CORPORACION HACIA UN VALLE SOLIDARIO (CHVS) - Sistema de Reserva de Salas

Este proyecto es una aplicación web moderna, elegante y 100% responsiva diseñada para gestionar la reserva de las salas de juntas **Amarilla** (con Internet) y **Morada**.

## Características
- **Calendario Visual Profesional:** Vista semanal y diaria adaptada para móviles y escritorio usando FullCalendar v6.
- **Identidad Corporativa:** Estilo Verde Esmeralda y Blanco.
- **Validación de Horarios:** Reservas restringidas entre **5:00 AM y 10:00 PM**.
- **Prevención de Conflictos:** El sistema no permite solapamientos en una misma sala.
- **Formulario Ágil:** Captura nombre, correo, área y detalles de la reserva sin necesidad de registro previo.

## Tecnologías Utilizadas
- **Backend:** FastAPI (Python)
- **Base de Datos:** PostgreSQL con SQLAlchemy ORM
- **Frontend:** Jinja2, Vanilla CSS (estilo Emerald), FullCalendar.js
- **Despliegue:** Railway.app y GitHub

## Configuración Local
1. Clonar el repositorio.
2. Crear un entorno virtual: `python -m venv venv`
3. Instalar dependencias: `pip install -r requirements.txt`
4. Configurar `DATABASE_URL` en el archivo `.env`.
5. Iniciar el servidor: `uvicorn app.main:app --reload`

## Despliegue en Railway
1. Conectar este repositorio a Railway.
2. Añadir un servicio de base de datos **PostgreSQL**.
3. Railway configurará automáticamente la variable `DATABASE_URL`.
4. El archivo `Procfile` y `railway.json` se encargarán del despliegue.

---
© 2026 CORPORACION HACIA UN VALLE SOLIDARIO (CHVS)
