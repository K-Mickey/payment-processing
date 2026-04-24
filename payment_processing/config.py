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

    host: str = "127.0.0.1"
    port: int = 8000
    workers: int = 1


class DBSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DB_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    user: str = "postgres"
    password: str = "postgres"
    name: str = "postgres"
    host: str = "localhost"
    port: int = 5432

    echo: bool = False
    pool_size: int = 5  # size of the connection pool
    max_overflow: int = 2  # amount of additional connections
    pool_timeout: int = 30  # seconds to wait for connection
    pool_recycle: int = 3600  # seconds to recycle a connection
    pool_pre_ping: bool = True  # check connection before use

    @property
    def dsn(self):
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    api_key: str = "secret"
    develop: bool = False

    log_level: str = "INFO"
    log_format: str = "> %(asctime)s %(levelname)s [%(filename)s - %(name)s - %(lineno)d] > %(message)s"

    broker_user: str = "guest"
    broker_password: str = "guest"
    broker_host: str = "localhost"
    broker_port: int = 5672

    outbox_producer_workers: int = 1
    outbox_pool_interval: float = 5
    outbox_batch_size: int = 5

    payment_consumer_workers: int = 1
    payment_processing_max_retries: int = 3
    payment_processing_base_delay: float = 1.0

    webhook_max_retries: int = 3
    webhook_base_delay: float = 1.0
    webhook_timeout: float = 10.0

    app: AppSettings = AppSettings()
    db: DBSettings = DBSettings()

    @property
    def broker_url(self):
        return f"amqp://{self.broker_user}:{self.broker_password}@{self.broker_host}:{self.broker_port}/"


settings = Settings()
