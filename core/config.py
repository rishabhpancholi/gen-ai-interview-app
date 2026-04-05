import logging
from typing import Protocol
from dataclasses import dataclass
from pydantic_settings import BaseSettings, SettingsConfigDict
from pymongo import AsyncMongoClient
from redis.asyncio import Redis

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

logger = logging.getLogger("uvicorn.error")


class Config(BaseSettings):
    mongo_db_cluster_name: str
    mongo_db_password: str
    mongo_db_database_name: str
    mongo_db_user_name: str
    jwt_secret_key: str
    redis_url: str
    redis_username: str
    redis_port: int
    redis_password: str
    fake_hash: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    groq_api_key: str
    groq_model: str

    @property
    def mongo_db_uri(self) -> str:
        return f"mongodb+srv://{self.mongo_db_user_name}:{self.mongo_db_password}@{self.mongo_db_cluster_name}.tmrtrob.mongodb.net/?appName={self.mongo_db_cluster_name}"

    model_config = SettingsConfigDict(env_file=".env")


@dataclass
class RedisConfig:
    host: str
    port: int
    username: str
    password: str


class LLM(Protocol):
    pass


@dataclass
class Clients:
    db_client: AsyncMongoClient
    redis_client: Redis
    llm: LLM


try:
    api_config = Config()
    logger.info("Configuration loaded successfully")
    redis_config = RedisConfig(
        host=api_config.redis_url,
        port=api_config.redis_port,
        username=api_config.redis_username,
        password=api_config.redis_password,
    )
except Exception:
    logger.exception("Failed to load configuration")
    raise
