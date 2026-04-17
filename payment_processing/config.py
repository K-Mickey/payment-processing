from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    title: str = "Payment Processing API"
    description: str = ""
    version: str = "0.1.0"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    api_prefix: str = "/api"


class DBSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DB_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    dsn: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    echo: bool = False
    pool_size: int = 5  # size of the connection pool
    max_overflow: int = 2  # amount of additional connections
    pool_timeout: int = 30  # seconds to wait for connection
    pool_recycle: int = 3600  # seconds to recycle a connection
    pool_pre_ping: bool = True  # check connection before use


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    develop: bool = False

    app: AppSettings = AppSettings()
    db: DBSettings = DBSettings()


settings = Settings()
