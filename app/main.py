from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date, time, datetime, timedelta
import os
from typing import List

from .database.db import engine, get_db, Base
from . import models, schemas

# Crear tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CHVS - Sala de Juntas")

# Archivos estáticos y plantillas
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Semilla inicial para las salas
@app.on_event("startup")
def startup_db_seed():
    db = next(get_db())
    # Verificar si ya existen salas
    if db.query(models.Room).count() == 0:
        rooms = [
            models.Room(name="Sala Amarilla", description="Conexión a Internet disponible", color="#FFD700"),
            models.Room(name="Sala Morada", description="Espacio tranquilo para reuniones", color="#800080")
        ]
        db.add_all(rooms)
        db.commit()

# Rutas
@app.get("/")
def read_root(request: Request, db: Session = Depends(get_db)):
    rooms = db.query(models.Room).all()
    return templates.TemplateResponse("index.html", {"request": request, "rooms": rooms})

@app.get("/api/bookings", response_model=List[schemas.Booking])
def get_bookings(db: Session = Depends(get_db)):
    return db.query(models.Booking).all()

@app.get("/api/rooms", response_model=List[schemas.Room])
def get_rooms(db: Session = Depends(get_db)):
    return db.query(models.Room).all()

@app.post("/api/bookings")
def create_booking(
    user_name: str = Form(...),
    user_email: str = Form(...),
    area: str = Form(...),
    booking_date: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    room_id: int = Form(...),
    db: Session = Depends(get_db)
):
    # Convertir strings a objetos datetime
    date_obj = date.fromisoformat(booking_date)
    start_obj = time.fromisoformat(start_time)
    end_obj = time.fromisoformat(end_time)

    # Validar horario (7am a 5pm)
    min_time = time(7, 0)
    max_time = time(17, 0)
    if start_obj < min_time or end_obj > max_time or start_obj >= end_obj:
        raise HTTPException(status_code=400, detail="Horario fuera del rango permitido (7:00 AM - 5:00 PM)")

    # Validar solapamiento
    existing_booking = db.query(models.Booking).filter(
        models.Booking.room_id == room_id,
        models.Booking.date == date_obj,
        models.Booking.start_time < end_obj,
        models.Booking.end_time > start_obj
    ).first()

    if existing_booking:
        raise HTTPException(status_code=400, detail="La sala ya está reservada en este horario.")

    new_booking = models.Booking(
        user_name=user_name,
        user_email=user_email,
        area=area,
        date=date_obj,
        start_time=start_obj,
        end_time=end_obj,
        room_id=room_id
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    return {"message": "Reserva creada con éxito", "booking": new_booking}
