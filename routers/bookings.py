from typing import List
from datetime import date
import schemas
import database

from fastapi import APIRouter, HTTPException, Depends, status
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


@router.post("/bookings", response_model=schemas.BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(booking_data: schemas.BookingCreate, current_user: dict = Depends(get_current_user)):
    """
    Создание бронирования. Доступно любому авторизованному пользователю.
    """
    slot_exists = any(slot["id"] == booking_data.slot_id for slot in database.SLOTS_DB)
    if not slot_exists:
        raise HTTPException(status_code=404, detail="Указанный временной слот не найден")

    for booking in database.BOOKINGS_DB:
        if booking["slot_id"] == booking_data.slot_id and booking["date"] == booking_data.date:
            raise HTTPException(
                status_code=400,
                detail="Этот временной слот на выбранную дату уже забронирован"
            )

    new_booking = {
        "id": database.booking_id_counter,
        "slot_id": booking_data.slot_id,
        "user_id": current_user["id"],
        "date": booking_data.date
    }
    database.BOOKINGS_DB.append(new_booking)
    database.booking_id_counter += 1

    return new_booking


@router.delete("/bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(booking_id: int, current_user: dict = Depends(get_current_user)):
    """
    Удаление бронирования.
    Сотрудник (employee) может удалить только свою бронь.
    Администратор (admin) может удалить любую бронь.
    """
    booking_to_delete = None
    for booking in database.BOOKINGS_DB:
        if booking["id"] == booking_id:
            booking_to_delete = booking
            break

    if not booking_to_delete:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")

    is_owner = booking_to_delete["user_id"] == current_user["id"]
    is_admin = current_user.get("role") == "admin"

    if not is_owner and not is_admin:
        raise HTTPException(
            status_code=403,
            detail="Недостаточно прав для удаления этого бронирования"
        )

    database.BOOKINGS_DB.remove(booking_to_delete)
    return
