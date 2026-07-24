from pydantic import BaseModel, ConfigDict
from datetime import date, time


class UserRegister(BaseModel):
    username: str
    password: str
    role: str = "employee"


class UserOut(BaseModel):
    id: int
    username: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class RoomOut(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class SlotOut(BaseModel):
    id: int
    room_id: int
    start_time: time
    end_time: time

    model_config = ConfigDict(from_attributes=True)


class SlotAvailabilityOut(BaseModel):
    slot_id: int
    start_time: time
    end_time: time
    is_available: bool


class BookingCreate(BaseModel):
    slot_id: int
    date: date


class BookingOut(BaseModel):
    id: int
    slot_id: int
    user_id: int
    booking_date: date

    model_config = ConfigDict(from_attributes=True)
