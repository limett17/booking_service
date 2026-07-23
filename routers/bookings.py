from fastapi import APIRouter, HTTPException, Depends
from datetime import date
import schemas
import database
from routers.auth import get_current_user

router = APIRouter(tags=["Bookings & Rooms"])


@router.get("/rooms", response_model=List[schemas.RoomOut])
def get_rooms():
    return database.ROOMS_DB


@router.get("/rooms/{room_id}/availability", response_model=List[schemas.SlotAvailabilityOut])
def get_room_availability(room_id: int, booking_date: date):
    room_exists = any(room["id"] == room_id for room in database.ROOMS_DB)
    if not room_exists:
        raise HTTPException(status_code=404, detail="Переговорная комната не найдена")

    room_slots = [slot for slot in database.SLOTS_DB if slot["room_id"] == room_id]
    booked_slot_ids = {b["slot_id"] for b in database.BOOKINGS_DB if b["date"] == booking_date}

    result = []
    for slot in room_slots:
        result.append({
            "slot_id": slot["id"],
            "start_time": slot["start_time"],
            "end_time": slot["end_time"],
            "is_available": slot["id"] not in booked_slot_ids
        })
    return result


@router.get("/users/me", response_model=schemas.UserOut)
def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user
