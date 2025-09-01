from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_PREFIX: str = "/api/v1"
    SERVICE_NAME: str = "glb2stl"
    ENV: str = "dev"  # dev|prod
    LOG_FORMAT: str = "console"  # console|json
    LOG_LEVEL: str = "INFO"

    MAX_BYTES: int = 50 * 1024 * 1024
    ENFORCE_Z_UP: bool = True  # Y-up → Z-up
    SCALE_TO_MM: bool = True  # meters → mm
    ALLOW_DECIMATE: bool = True
    MAX_FACES_BEFORE_DECIMATE: int = 2_000_000

    CORS_ALLOW_ALL: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
