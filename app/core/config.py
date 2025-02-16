from pydantic import RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


MERCH_PRICES = {
    "t-shirt": 80,
    "cup": 20,
    "book": 50,
    "pen": 10,
    "powerbank": 200,
    "hoody": 300,
    "umbrella": 200,
    "socks": 10,
    "wallet": 50,
    "pink-hoody": 500
}


class Settings(BaseSettings):
    PROJECT_NAME: str = "Merchant Shop API"
    PROJECT_VERSION: str = "1.0.0"

    POSTGRES_URL: str
    REDIS_URL: RedisDsn
    SECRET_KEY: SecretStr
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file='.env',
        env_file_encoding='utf-8'
    )

settings = Settings()
