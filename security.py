from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
import bcrypt
from config import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def hash_password(password: str) -> str:
    """Превращает чистый текстовый пароль в безопасный хэш"""
    # 1. bcrypt работает со строками байт, поэтому кодируем пароль в utf-8
    password_bytes = password.encode('utf-8')

    # 2. Генерируем "соль" (случайный шум для защиты от подбора)
    salt = bcrypt.gensalt()

    # 3. Хэшируем и превращаем обратно в обычную строку для хранения
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    return hashed_bytes.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет, совпадает ли введенный пароль с сохраненным хэшем"""
    # Переводим и чистый пароль, и сохраненный хэш в байты перед сверкой
    plain_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')

    # Метод checkpw сам знает, как вытащить соль из хэша и сравнить
    return bcrypt.checkpw(plain_bytes, hashed_bytes)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создает JWT-токен, который действует ограниченное время"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Расшифровывает JWT-токен и проверяет его валидность"""
    try:
        # Расшифровываем токен с помощью нашего секретного ключа
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        # Если токен протух, изменен или сломан — возвращаем None
        return None
