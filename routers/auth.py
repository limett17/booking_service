from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
import security
import schemas
import database

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
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

    for user in database.USERS_DB:
        if user["username"] == username:
            return user

    raise credentials_exception


@router.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register(user_data: schemas.UserRegister):
    for user in database.USERS_DB:
        if user["username"] == user_data.username:
            raise HTTPException(status_code=400, detail="Пользователь уже существует")

    hashed_pwd = security.hash_password(user_data.password)

    new_user = {
        "id": database.user_id_counter,
        "username": user_data.username,
        "password_hash": hashed_pwd,
        "role": user_data.role
    }
    database.USERS_DB.append(new_user)
    database.user_id_counter += 1
    return new_user


@router.post("/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_found = None
    for user in database.USERS_DB:
        if user["username"] == form_data.username:
            user_found = user
            break

    if not user_found or not security.verify_password(form_data.password, user_found["password_hash"]):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    token_data = {"sub": user_found["username"], "role": user_found["role"]}
    access_token = security.create_access_token(data=token_data)
    return {"access_token": access_token, "token_type": "bearer"}
