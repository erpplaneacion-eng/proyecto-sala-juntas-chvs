from datetime import date, datetime, time, timedelta
import base64
import os
import secrets
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import text
from sqlalchemy.orm import Session

from . import models, schemas
from .auth import (
    create_session_token,
    get_current_admin,
    hash_password,
    verify_password,
)
from .config import load_environment
from .database.db import Base, engine, get_db

load_environment()

# ---------------------------------------------------------------------------
# Gmail API — envío via OAuth2 (funciona en Railway, no usa SMTP saliente)
# ---------------------------------------------------------------------------

def _str_to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("true", "1", "yes")


def _build_gmail_service():
    """Construye el cliente de la Gmail API usando el Refresh Token del entorno."""
    creds = Credentials(
        token=None,
        refresh_token=os.getenv("GMAIL_REFRESH_TOKEN"),
        client_id=os.getenv("GMAIL_CLIENT_ID"),
        client_secret=os.getenv("GMAIL_CLIENT_SECRET"),
        token_uri="https://oauth2.googleapis.com/token",
    )
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def _render_email_template(template_name: str, context: dict) -> str:
    """Renderiza una plantilla Jinja2 y devuelve el HTML como string."""
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template(template_name)
    return template.render(**context)


def _create_mime_message(sender: str, to: str, subject: str, html_body: str) -> dict:
    """Crea el mensaje MIME codificado en base64 para la Gmail API."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {"raw": raw}


async def send_booking_email(booking_data: dict, email_to: str):
    """Envía el correo de confirmación usando la Gmail API (OAuth2).

    Respeta MAIL_ENABLED: si es False, omite el envío silenciosamente.
    """
    if not _str_to_bool(os.getenv("MAIL_ENABLED"), default=False):
        print("[INFO] Envío de correo deshabilitado (MAIL_ENABLED=False).")
        return

    sender = os.getenv("MAIL_FROM", os.getenv("MAIL_USERNAME"))
    subject = f"Confirmación de Reserva: {booking_data['room_name']}"

    try:
        html_body = _render_email_template("email_booking.html", booking_data)
        service = _build_gmail_service()
        message = _create_mime_message(sender, email_to, subject, html_body)
        service.users().messages().send(userId="me", body=message).execute()
        print(f"[INFO] Correo enviado vía Gmail API a {email_to}")
    except HttpError as e:
        print(f"[ERROR] Gmail API HttpError al enviar a {email_to}: {e}")
    except Exception as e:
        print(f"[ERROR] No se pudo enviar el correo a {email_to}: {e}")


# ---------------------------------------------------------------------------
# App FastAPI
# ---------------------------------------------------------------------------
app = FastAPI(title="CHVS - Sala de Juntas")

# Archivos estaticos y plantillas
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
def startup_db_seed():
    """Crea tablas, salas y el usuario admin por defecto si no existen."""
    Base.metadata.create_all(bind=engine)
    db_gen = get_db()
    db = next(db_gen)
    try:
        # Migraciones para columnas nuevas (seguro si ya existen)
        for sql in [
            "ALTER TABLE rooms ADD COLUMN capacity INTEGER DEFAULT 10",
            "ALTER TABLE bookings ADD COLUMN attendees INTEGER DEFAULT 1",
            "ALTER TABLE bookings ADD COLUMN cancel_token VARCHAR(64)",
            "ALTER TABLE bookings ADD COLUMN cancel_token_expires_at TIMESTAMP",
        ]:
            try:
                db.execute(text(sql))
                db.commit()
            except Exception:
                db.rollback()

        # Seed de salas
        if db.query(models.Room).count() == 0:
            rooms = [
                models.Room(
                    name="Sala Amarilla",
                    description="Conexion a Internet disponible",
                    color="#FFD700",
                    capacity=12,
                ),
                models.Room(
                    name="Sala Morada",
                    description="Espacio tranquilo para reuniones",
                    color="#800080",
                    capacity=8,
                ),
            ]
            db.add_all(rooms)
            db.commit()
        else:
            # Actualizar capacidades de salas existentes
            try:
                db.execute(text("UPDATE rooms SET capacity = 12 WHERE name = 'Sala Amarilla'"))
                db.execute(text("UPDATE rooms SET capacity = 8 WHERE name = 'Sala Morada'"))
                db.commit()
            except Exception:
                db.rollback()

        # Seed del administrador
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "Chvs@2026#Admin!")
        if db.query(models.AdminUser).filter_by(username=admin_username).first() is None:
            admin = models.AdminUser(
                username=admin_username,
                hashed_password=hash_password(admin_password),
            )
            db.add(admin)
            db.commit()
            print(f"[INFO] Usuario admin '{admin_username}' creado exitosamente.")
    finally:
        db_gen.close()


# ---------------------------------------------------------------------------
# Rutas públicas
# ---------------------------------------------------------------------------

@app.get("/")
def read_root(request: Request, db: Session = Depends(get_db)):
    rooms = db.query(models.Room).all()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "rooms": rooms, "now": date.today().isoformat()},
    )


@app.get("/api/bookings", response_model=List[schemas.Booking])
def get_bookings(db: Session = Depends(get_db)):
    return db.query(models.Booking).all()


@app.get("/api/rooms", response_model=List[schemas.Room])
def get_rooms(db: Session = Depends(get_db)):
    return db.query(models.Room).all()


@app.post("/api/bookings")
async def create_booking(
    request: Request,
    background_tasks: BackgroundTasks,
    user_name: str = Form(...),
    user_email: str = Form(...),
    area: str = Form(...),
    booking_date: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    room_id: int = Form(...),
    attendees: int = Form(...),
    db: Session = Depends(get_db),
):
    # Convertir strings a objetos date/time
    date_obj = date.fromisoformat(booking_date)
    start_obj = time.fromisoformat(start_time)
    end_obj = time.fromisoformat(end_time)

    # Validar horario (7am a 5pm)
    min_time = time(7, 0)
    max_time = time(17, 0)
    if start_obj < min_time or end_obj > max_time or start_obj >= end_obj:
        raise HTTPException(
            status_code=400,
            detail="Horario fuera del rango permitido (7:00 AM - 5:00 PM)",
        )

    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if room is None:
        raise HTTPException(status_code=404, detail="La sala seleccionada no existe.")

    # Validar capacidad
    if attendees < 1 or (room.capacity and attendees > room.capacity):
        raise HTTPException(
            status_code=400,
            detail=f"Número de asistentes inválido. La sala tiene capacidad para {room.capacity} personas.",
        )

    # Validar solapamiento
    existing_booking = (
        db.query(models.Booking)
        .filter(
            models.Booking.room_id == room_id,
            models.Booking.date == date_obj,
            models.Booking.start_time < end_obj,
            models.Booking.end_time > start_obj,
        )
        .first()
    )

    if existing_booking:
        raise HTTPException(
            status_code=400, detail="La sala ya esta reservada en este horario."
        )

    cancel_token = secrets.token_urlsafe(32)
    cancel_token_expires_at = datetime.utcnow() + timedelta(hours=48)

    new_booking = models.Booking(
        user_name=user_name,
        user_email=user_email,
        area=area,
        date=date_obj,
        start_time=start_obj,
        end_time=end_obj,
        room_id=room_id,
        attendees=attendees,
        cancel_token=cancel_token,
        cancel_token_expires_at=cancel_token_expires_at,
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    base_url = str(request.base_url).rstrip("/")
    email_data = {
        "user_name": user_name,
        "room_name": room.name,
        "booking_date": booking_date,
        "start_time": start_time,
        "end_time": end_time,
        "area": area,
        "attendees": attendees,
        "cancel_url": f"{base_url}/cancelar/{cancel_token}",
    }
    background_tasks.add_task(send_booking_email, email_data, user_email)

    return {"message": "Reserva creada con exito", "booking": new_booking}


# ---------------------------------------------------------------------------
# Rutas de autenticación admin
# ---------------------------------------------------------------------------

@app.get("/admin/login")
def admin_login_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": None})


@app.post("/admin/login")
def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(models.AdminUser).filter_by(username=username, is_active=True).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "admin_login.html",
            {"request": request, "error": "Usuario o contraseña incorrectos."},
            status_code=401,
        )
    token = create_session_token(username)
    response = RedirectResponse(url="/admin", status_code=302)
    response.set_cookie(
        key="admin_session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=8 * 3600,  # 8 horas
    )
    return response


@app.get("/admin/logout")
def admin_logout():
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("admin_session")
    return response


# ---------------------------------------------------------------------------
# Panel de administración (protegido)
# ---------------------------------------------------------------------------

@app.get("/admin")
def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin),
    sala: Optional[int] = None,
    fecha: Optional[str] = None,
):
    query = db.query(models.Booking)
    if sala:
        query = query.filter(models.Booking.room_id == sala)
    if fecha:
        try:
            query = query.filter(models.Booking.date == date.fromisoformat(fecha))
        except ValueError:
            pass
    bookings = query.order_by(models.Booking.date.desc(), models.Booking.start_time).all()
    rooms = db.query(models.Room).all()
    return templates.TemplateResponse(
        "admin_dashboard.html",
        {
            "request": request,
            "bookings": bookings,
            "rooms": rooms,
            "admin_user": current_admin,
            "filter_sala": sala,
            "filter_fecha": fecha,
        },
    )


@app.get("/admin/bookings/new")
def admin_new_booking_form(
    request: Request,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin),
):
    rooms = db.query(models.Room).all()
    return templates.TemplateResponse(
        "admin_edit_booking.html",
        {
            "request": request,
            "booking": None,
            "rooms": rooms,
            "admin_user": current_admin,
            "action": "/admin/bookings/new",
            "title": "Nueva Reserva",
        },
    )


@app.post("/admin/bookings/new")
def admin_create_booking(
    request: Request,
    background_tasks: BackgroundTasks,
    user_name: str = Form(...),
    user_email: str = Form(...),
    area: str = Form(...),
    booking_date: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    room_id: int = Form(...),
    attendees: int = Form(...),
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin),
):
    date_obj = date.fromisoformat(booking_date)
    start_obj = time.fromisoformat(start_time)
    end_obj = time.fromisoformat(end_time)

    min_time = time(7, 0)
    max_time = time(17, 0)
    if start_obj < min_time or end_obj > max_time or start_obj >= end_obj:
        rooms = db.query(models.Room).all()
        return templates.TemplateResponse(
            "admin_edit_booking.html",
            {
                "request": request,
                "booking": None,
                "rooms": rooms,
                "admin_user": current_admin,
                "action": "/admin/bookings/new",
                "title": "Nueva Reserva",
                "error": "Horario fuera del rango permitido (7:00 AM - 5:00 PM).",
            },
            status_code=400,
        )

    room = db.query(models.Room).filter(models.Room.id == room_id).first()

    if room and attendees > (room.capacity or 9999):
        rooms = db.query(models.Room).all()
        return templates.TemplateResponse(
            "admin_edit_booking.html",
            {
                "request": request,
                "booking": None,
                "rooms": rooms,
                "admin_user": current_admin,
                "action": "/admin/bookings/new",
                "title": "Nueva Reserva",
                "error": f"Número de asistentes supera la capacidad de la sala ({room.capacity} personas).",
            },
            status_code=400,
        )

    existing = (
        db.query(models.Booking)
        .filter(
            models.Booking.room_id == room_id,
            models.Booking.date == date_obj,
            models.Booking.start_time < end_obj,
            models.Booking.end_time > start_obj,
        )
        .first()
    )
    if existing:
        rooms = db.query(models.Room).all()
        return templates.TemplateResponse(
            "admin_edit_booking.html",
            {
                "request": request,
                "booking": None,
                "rooms": rooms,
                "admin_user": current_admin,
                "action": "/admin/bookings/new",
                "title": "Nueva Reserva",
                "error": "La sala ya está reservada en ese horario.",
            },
            status_code=400,
        )

    cancel_token = secrets.token_urlsafe(32)
    cancel_token_expires_at = datetime.utcnow() + timedelta(hours=48)

    new_booking = models.Booking(
        user_name=user_name,
        user_email=user_email,
        area=area,
        date=date_obj,
        start_time=start_obj,
        end_time=end_obj,
        room_id=room_id,
        attendees=attendees,
        cancel_token=cancel_token,
        cancel_token_expires_at=cancel_token_expires_at,
    )
    db.add(new_booking)
    db.commit()

    base_url = str(request.base_url).rstrip("/")
    email_data = {
        "user_name": user_name,
        "room_name": room.name if room else "Sala",
        "booking_date": booking_date,
        "start_time": start_time,
        "end_time": end_time,
        "area": area,
        "attendees": attendees,
        "cancel_url": f"{base_url}/cancelar/{cancel_token}",
    }
    background_tasks.add_task(send_booking_email, email_data, user_email)

    return RedirectResponse(url="/admin", status_code=302)


@app.get("/admin/bookings/{booking_id}/edit")
def admin_edit_booking_form(
    booking_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin),
):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Reserva no encontrada.")
    rooms = db.query(models.Room).all()
    return templates.TemplateResponse(
        "admin_edit_booking.html",
        {
            "request": request,
            "booking": booking,
            "rooms": rooms,
            "admin_user": current_admin,
            "action": f"/admin/bookings/{booking_id}/edit",
            "title": "Editar Reserva",
            "error": None,
        },
    )


@app.post("/admin/bookings/{booking_id}/edit")
def admin_update_booking(
    booking_id: int,
    request: Request,
    user_name: str = Form(...),
    user_email: str = Form(...),
    area: str = Form(...),
    booking_date: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    room_id: int = Form(...),
    attendees: int = Form(...),
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin),
):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Reserva no encontrada.")

    date_obj = date.fromisoformat(booking_date)
    start_obj = time.fromisoformat(start_time)
    end_obj = time.fromisoformat(end_time)

    min_time = time(7, 0)
    max_time = time(17, 0)
    if start_obj < min_time or end_obj > max_time or start_obj >= end_obj:
        rooms = db.query(models.Room).all()
        return templates.TemplateResponse(
            "admin_edit_booking.html",
            {
                "request": request,
                "booking": booking,
                "rooms": rooms,
                "admin_user": current_admin,
                "action": f"/admin/bookings/{booking_id}/edit",
                "title": "Editar Reserva",
                "error": "Horario fuera del rango permitido (7:00 AM - 5:00 PM).",
            },
            status_code=400,
        )

    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if room and attendees > (room.capacity or 9999):
        rooms = db.query(models.Room).all()
        return templates.TemplateResponse(
            "admin_edit_booking.html",
            {
                "request": request,
                "booking": booking,
                "rooms": rooms,
                "admin_user": current_admin,
                "action": f"/admin/bookings/{booking_id}/edit",
                "title": "Editar Reserva",
                "error": f"Número de asistentes supera la capacidad de la sala ({room.capacity} personas).",
            },
            status_code=400,
        )

    # Validar solapamiento (excluyendo la misma reserva)
    existing = (
        db.query(models.Booking)
        .filter(
            models.Booking.id != booking_id,
            models.Booking.room_id == room_id,
            models.Booking.date == date_obj,
            models.Booking.start_time < end_obj,
            models.Booking.end_time > start_obj,
        )
        .first()
    )
    if existing:
        rooms = db.query(models.Room).all()
        return templates.TemplateResponse(
            "admin_edit_booking.html",
            {
                "request": request,
                "booking": booking,
                "rooms": rooms,
                "admin_user": current_admin,
                "action": f"/admin/bookings/{booking_id}/edit",
                "title": "Editar Reserva",
                "error": "La sala ya está reservada en ese horario.",
            },
            status_code=400,
        )

    booking.user_name = user_name
    booking.user_email = user_email
    booking.area = area
    booking.date = date_obj
    booking.start_time = start_obj
    booking.end_time = end_obj
    booking.room_id = room_id
    booking.attendees = attendees
    db.commit()

    return RedirectResponse(url="/admin", status_code=302)


@app.post("/admin/bookings/{booking_id}/delete")
def admin_delete_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin),
):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Reserva no encontrada.")
    db.delete(booking)
    db.commit()
    return RedirectResponse(url="/admin", status_code=302)


# ---------------------------------------------------------------------------
# Cancelación de reserva por el usuario (enlace en el email)
# ---------------------------------------------------------------------------

@app.get("/cancelar/{token}")
def cancel_booking_form(token: str, request: Request, db: Session = Depends(get_db)):
    booking = db.query(models.Booking).filter(models.Booking.cancel_token == token).first()

    if not booking:
        return templates.TemplateResponse(
            "cancel_result.html",
            {"request": request, "success": False, "error": "Reserva no encontrada o ya fue cancelada."},
        )

    if booking.cancel_token_expires_at and datetime.utcnow() > booking.cancel_token_expires_at:
        return templates.TemplateResponse(
            "cancel_result.html",
            {"request": request, "success": False, "error": "El enlace de cancelación ha expirado (válido por 48 horas)."},
        )

    return templates.TemplateResponse(
        "cancel_confirm.html",
        {"request": request, "booking": booking, "token": token},
    )


@app.post("/cancelar/{token}")
def cancel_booking_confirm(token: str, request: Request, db: Session = Depends(get_db)):
    booking = db.query(models.Booking).filter(models.Booking.cancel_token == token).first()

    if not booking:
        return templates.TemplateResponse(
            "cancel_result.html",
            {"request": request, "success": False, "error": "Reserva no encontrada o ya fue cancelada."},
        )

    if booking.cancel_token_expires_at and datetime.utcnow() > booking.cancel_token_expires_at:
        return templates.TemplateResponse(
            "cancel_result.html",
            {"request": request, "success": False, "error": "El enlace de cancelación ha expirado."},
        )

    db.delete(booking)
    db.commit()

    return templates.TemplateResponse(
        "cancel_result.html",
        {"request": request, "success": True, "error": None},
    )
