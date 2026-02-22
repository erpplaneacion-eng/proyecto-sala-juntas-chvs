from datetime import date, time
import os
from typing import List

from fastapi import BackgroundTasks, Depends, FastAPI, Form, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from sqlalchemy.orm import Session

from . import models, schemas
from .config import load_environment
from .database.db import Base, engine, get_db

load_environment()

# Configuracion de correo — los valores se leen del .env para que local y Railway
# puedan usar configuraciones distintas (587/STARTTLS vs 465/SSL).
def _str_to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("true", "1", "yes")

mail_conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM", os.getenv("MAIL_USERNAME")),
    MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_STARTTLS=_str_to_bool(os.getenv("MAIL_STARTTLS"), default=True),
    MAIL_SSL_TLS=_str_to_bool(os.getenv("MAIL_SSL_TLS"), default=False),
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER="app/templates",
)

fastmail = FastMail(mail_conf)


async def send_booking_email(booking_data: dict, email_to: str):
    """Send booking confirmation email in background.
    
    Respeta la variable MAIL_ENABLED del entorno: si es False, no envía nada.
    """
    if not _str_to_bool(os.getenv("MAIL_ENABLED"), default=False):
        print("[INFO] Envío de correo deshabilitado (MAIL_ENABLED=False). Se omite el correo.")
        return

    try:
        message = MessageSchema(
            subject=f"Confirmacion de Reserva: {booking_data['room_name']}",
            recipients=[email_to],
            template_body=booking_data,
            subtype=MessageType.html,
        )
        await fastmail.send_message(message, template_name="email_booking.html")
        print(f"[INFO] Correo de confirmación enviado a {email_to}")
    except Exception as e:
        print(f"[ERROR] No se pudo enviar el correo a {email_to}: {e}")


app = FastAPI(title="CHVS - Sala de Juntas")

# Archivos estaticos y plantillas
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
def startup_db_seed():
    """Create tables and seed default rooms when empty."""
    Base.metadata.create_all(bind=engine)
    db_gen = get_db()
    db = next(db_gen)
    try:
        if db.query(models.Room).count() == 0:
            rooms = [
                models.Room(
                    name="Sala Amarilla",
                    description="Conexion a Internet disponible",
                    color="#FFD700",
                ),
                models.Room(
                    name="Sala Morada",
                    description="Espacio tranquilo para reuniones",
                    color="#800080",
                ),
            ]
            db.add_all(rooms)
            db.commit()
    finally:
        db_gen.close()


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
    background_tasks: BackgroundTasks,
    user_name: str = Form(...),
    user_email: str = Form(...),
    area: str = Form(...),
    booking_date: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    room_id: int = Form(...),
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

    new_booking = models.Booking(
        user_name=user_name,
        user_email=user_email,
        area=area,
        date=date_obj,
        start_time=start_obj,
        end_time=end_obj,
        room_id=room_id,
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    email_data = {
        "user_name": user_name,
        "room_name": room.name,
        "booking_date": booking_date,
        "start_time": start_time,
        "end_time": end_time,
        "area": area,
    }
    background_tasks.add_task(send_booking_email, email_data, user_email)

    return {"message": "Reserva creada con exito", "booking": new_booking}
