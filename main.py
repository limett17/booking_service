from fastapi import FastAPI
from contextlib import contextmanager
from datetime import time
import database
from routers import auth, bookings


@contextmanager
def lifespan(app: FastAPI):
    database.ROOMS_DB.clear()
    database.SLOTS_DB.clear()

    database.ROOMS_DB.append({"id": 1, "name": "Переговорная Альфа"})
    database.ROOMS_DB.append({"id": 2, "name": "Переговорная Бета"})

    working_hours = [
        (time(9, 0), time(11, 0)),
        (time(11, 0), time(13, 0)),
        (time(14, 0), time(16, 0)),
        (time(16, 0), time(18, 0)),
    ]

    slot_id_counter = 1
    for room in database.ROOMS_DB:
        for start, end in working_hours:
            database.SLOTS_DB.append({
                "id": slot_id_counter,
                "room_id": room["id"],
                "start_time": start,
                "end_time": end
            })
            slot_id_counter += 1

    yield
    pass


app = FastAPI(title="Booking System", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(bookings.router)
