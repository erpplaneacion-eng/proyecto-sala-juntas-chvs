from pydantic import BaseModel, EmailStr
from datetime import date, time, datetime
from typing import Optional, List

class RoomBase(BaseModel):
    name: str
    description: Optional[str] = None
    color: str

class Room(RoomBase):
    id: int
    class Config:
        from_attributes = True

class BookingBase(BaseModel):
    user_name: str
    user_email: str
    area: str
    date: date
    start_time: time
    end_time: time
    room_id: int

class BookingCreate(BookingBase):
    pass

class Booking(BookingBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class BookingUpdate(BaseModel):
    """Schema para edición parcial de reservas por el administrador."""
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    area: Optional[str] = None
    date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    room_id: Optional[int] = None
