from pydantic import BaseModel
from datetime import date, time


class UserRegister(BaseModel):
    username: str
    password: str
    role: str = "employee"


class UserOut(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class RoomOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class SlotOut(BaseModel):
    id: int
    room_id: int
    start_time: time
    end_time: time

    class Config:
        from_attributes = True


class SlotAvailabilityOut(BaseModel):
    slot_id: int
    start_time: time
    end_time: time
    is_available: bool
