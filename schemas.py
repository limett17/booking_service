from pydantic import BaseModel

class UserRegister(BaseModel):
    username: str
    password: str
    role: str = "employee"  # По умолчанию роль — сотрудник, но можно передать "admin"

class UserOut(BaseModel):
    id: int
    username: str
    role: str

    # Этот подкласс нужен, чтобы Pydantic умел читать данные не только из словарей, но и из объектов (пригодится для БД)
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
