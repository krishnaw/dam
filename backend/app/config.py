from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://dam:dam_dev_password@localhost:5432/dam"
    REDIS_URL: str = "redis://localhost:6379/0"
    MEILISEARCH_URL: str = "http://localhost:7700"
    MEILISEARCH_KEY: str = "dam_dev_meili_key"
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "dam_dev_user"
    MINIO_SECRET_KEY: str = "dam_dev_password"
    MINIO_BUCKET: str = "dam-assets"
    MINIO_SECURE: bool = False
    JWT_SECRET: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 60
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CEREBRAS_API_KEY: str = ""
    MISTRAL_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:3001/auth/google/callback"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
