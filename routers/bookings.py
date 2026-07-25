from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import date
from typing import List

import schemas
import database
import models
from routers.auth import get_current_user

router = APIRouter(tags=["Bookings & Rooms"])


@router.get("/rooms", response_model=List[schemas.RoomOut])
async def get_rooms(db: AsyncSession = Depends(database.get_db)):
    """Возвращает список всех комнат из PostgreSQL"""
    result = await db.execute(select(models.RoomModel))
    return result.scalars().all()


@router.get("/rooms/{room_id}/availability", response_model=List[schemas.SlotAvailabilityOut])
async def get_room_availability(
    room_id: int,
    booking_date: date,
    db: AsyncSession = Depends(database.get_db)
):
    """Формирует сетку слотов для комнаты на выбранную дату из БД"""
    room_result = await db.execute(select(models.RoomModel).where(models.RoomModel.id == room_id))
    if not room_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Переговорная комната не найдена")

    slots_result = await db.execute(
        select(models.SlotModel).where(models.SlotModel.room_id == room_id)
    )
    room_slots = slots_result.scalars().all()

    bookings_result = await db.execute(
        select(models.BookingModel.slot_id).where(models.BookingModel.booking_date == booking_date)
    )
    booked_slot_ids = set(bookings_result.scalars().all())

    result = []
    for slot in room_slots:
        result.append({
            "slot_id": slot.id,
            "start_time": slot.start_time,
            "end_time": slot.end_time,
            "is_available": slot.id not in booked_slot_ids
        })
    return result


@router.get("/users/me", response_model=schemas.UserOut)
def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.post("/bookings", response_model=schemas.BookingOut, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: schemas.BookingCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
):
    """Создает бронирование в PostgreSQL с проверкой доступности"""
    slot_result = await db.execute(
        select(models.SlotModel).where(models.SlotModel.id == booking_data.slot_id)
    )
    if not slot_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Указанный временной слот не найден")

    existing_booking_result = await db.execute(
        select(models.BookingModel).where(
            and_(
                models.BookingModel.slot_id == booking_data.slot_id,
                models.BookingModel.booking_date == booking_data.date
            )
        )
    )
    if existing_booking_result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Этот временной слот на выбранную дату уже забронирован"
        )

    new_booking = models.BookingModel(
        slot_id=booking_data.slot_id,
        user_id=current_user["id"],
        booking_date=booking_data.date
    )
    db.add(new_booking)
    await db.commit()
    await db.refresh(new_booking)

    return new_booking


@router.delete("/bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booking(
    booking_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
):
    """Удаление бронирования с проверкой ролей (сотрудник/админ)"""
    result = await db.execute(select(models.BookingModel).where(models.BookingModel.id == booking_id))
    booking_to_delete = result.scalar_one_or_none()

    if not booking_to_delete:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")

    is_owner = booking_to_delete.user_id == current_user["id"]
    is_admin = current_user.get("role") == models.UserRole.ADMIN

    if not is_owner and not is_admin:
        raise HTTPException(
            status_code=403,
            detail="Недостаточно прав для удаления этого бронирования"
        )

    await db.delete(booking_to_delete)
    await db.commit()
    return
