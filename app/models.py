from sqlalchemy import Column, Integer, String, Date, Time, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from .database.db import Base
import datetime

class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    color = Column(String)  # Para identificar visualmente en el calendario

    bookings = relationship("Booking", back_populates="room")

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, index=True)
    user_email = Column(String, index=True)
    area = Column(String)
    date = Column(Date, index=True)
    start_time = Column(Time)
    end_time = Column(Time)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    room_id = Column(Integer, ForeignKey("rooms.id"))
    room = relationship("Room", back_populates="bookings")


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
