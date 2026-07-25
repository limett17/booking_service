from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import security
import schemas
import database
import models

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(database.get_db)
) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось валидировать учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = security.decode_access_token(token)
    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    result = await db.execute(select(models.UserModel).where(models.UserModel.username == username))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return {"id": user.id, "username": user.username, "role": user.role}


@router.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_data: schemas.UserRegister, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.UserModel).where(models.UserModel.username == user_data.username))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь уже существует")

    hashed_pwd = security.hash_password(user_data.password)

    new_user = models.UserModel(
        username=user_data.username,
        password_hash=hashed_pwd,
        role=user_data.role
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post("/token", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(database.get_db)):
    """Аутентификация и выдача JWT-токена на основе данных из PostgreSQL"""
    result = await db.execute(select(models.UserModel).where(models.UserModel.username == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    token_data = {"sub": user.username, "role": user.role}
    access_token = security.create_access_token(data=token_data)

    return {"access_token": access_token, "token_type": "bearer"}
