from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")

    title: str = "Payment Processing API"
    description: str = ""
    version: str = "0.1.0"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"


class Settings(BaseSettings):
    develop: bool = False

    app: AppSettings = AppSettings()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
