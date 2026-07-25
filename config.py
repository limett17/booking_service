from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: str

    # Добавляем extra="ignore", чтобы он не падал из-за наличия DB_USER, DB_PASSWORD и т.д.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
