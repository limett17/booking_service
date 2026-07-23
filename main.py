from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.security import OAuth2PasswordBearer
import security
import schemas

app = FastAPI(title="Booking System Auth MVP")

# Наша временная база данных в памяти
USERS_DB = []
# Счетчик для генерации ID пользователей
user_id_counter = 1

# Указываем FastAPI, где именно брать токен при авторизации
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Эта функция — зависимость. Она извлекает пользователя из токена.
    Если токен невалидный, она сразу прерывает запрос и возвращает 401.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось валидировать учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Расшифровываем токен
    payload = security.decode_access_token(token)
    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    role: str = payload.get("role")

    if username is None or role is None:
        raise credentials_exception

    # 2. Ищем пользователя в нашей базе данных
    user_found = None
    for user in USERS_DB:
        if user["username"] == username:
            user_found = user
            break

    if user_found is None:
        raise credentials_exception

    return user_found


@app.post("/auth/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register(user_data: schemas.UserRegister):
    global user_id_counter

    # 1. Проверяем, нет ли уже пользователя с таким именем
    for user in USERS_DB:
        if user["username"] == user_data.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким именем уже существует"
            )

    # 2. Хэшируем пароль
    hashed_pwd = security.hash_password(user_data.password)

    # 3. Создаем "запись" в нашей базе
    new_user = {
        "id": user_id_counter,
        "username": user_data.username,
        "password_hash": hashed_pwd,
        "role": user_data.role
    }
    USERS_DB.append(new_user)
    user_id_counter += 1

    return new_user


@app.post("/auth/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2PasswordRequestForm — это встроенный инструмент FastAPI.
    Он ожидает данные не в JSON, а в формате form-data (поля username и password).
    Это стандарт для Swagger UI.
    """
    # 1. Ищем пользователя в нашей базе
    user_found = None
    for user in USERS_DB:
        if user["username"] == form_data.username:
            user_found = user
            break

    # 2. Если не нашли или пароль не совпал — кидаем ошибку
    if not user_found or not security.verify_password(form_data.password, user_found["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Если все ок, создаем токен. Внутрь токена (sub) зашиваем username и role
    token_data = {"sub": user_found["username"], "role": user_found["role"]}
    access_token = security.create_access_token(data=token_data)

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=schemas.UserOut)
def read_users_me(current_user: dict = Depends(get_current_user)):
    """
    Этот роут защищен! Обратите внимание на Depends(get_current_user).
    FastAPI сначала выполнит нашу функцию get_current_user,
    и если всё ок, передаст пользователя в переменную current_user.
    """
    return current_user
