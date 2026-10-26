from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Amrutam Telemedicine API"
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "amrutam-telemedicine-super-secret-key-32bytes"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str = "sqlite:///./amrutam.db"
    RATE_LIMIT_PER_MINUTE: int = 120
    API_V1_PREFIX: str = "/api/v1"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
