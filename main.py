from fastapi import FastAPI
from contextlib import asynccontextmanager

from routers import auth, bookings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print('Запуск')
    yield
    pass


app = FastAPI(title="Booking System", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(bookings.router)
