# Booking System API

Асинхронное REST API приложение для бронирования переговорных комнат.

## Cтек
* **Фреймворк:** FastAPI (Python 3.12)
* **База данных:** PostgreSQL 15 (Asyncpg)
* **ORM:** SQLAlchemy 2.0
* **Миграции баз данных:** Alembic
* **Управление зависимостями:** Poetry
* **Контейнеризация:** Docker / Docker Compose
* **Тестирование:** Pytest + HTTPX + Aiosqlite


## Запуск
В Docker: 
1. Убедитесь, что запущен **Docker Desktop**.
2. Создайте локальный файл `.env` в корне проекта (на базе `.env.example`).
3. Выполните команду в терминале:
```bash
docker compose up --build
```

Локально:
1. Убедитесь, что запущен контейнер с базой данных:
```bash
docker compose up -d postgres_db
```
2. Установите зависимости проекта через Poetry:
```bash
poetry install
```
3. Примените миграции Alembic для настройки структуры таблиц:
```bash
poetry run alembic upgrade head
```
4. Запустите локальный сервер разработки Uvicorn:
```bash
poetry run uvicorn main:app --reload
```

После запуска интерактивная документация API (Swagger UI) будет доступна по адресу:
**[http://127.0.0.1:8000/docs#/](http://127.0.0.1:8000/docs#/)**

## Запуск автотестов и замер покрытия
Тесты используют изолированную базу данных SQLite в памяти и не затрагивают данные в PostgreSQL.
Для запуска тестов и генерации test coverage выполните локально:

```bash
poetry run pytest --cov=routers --cov=main --cov-report=term-missing
```
