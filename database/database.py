import logging
from redis.asyncio import Redis
from pymongo.server_api import ServerApi
from pymongo import AsyncMongoClient
from core import RedisConfig

logger = logging.getLogger("uvicorn.error")


async def connect_db(db_uri: str) -> AsyncMongoClient:
    client = AsyncMongoClient(db_uri, server_api=ServerApi("1"))

    try:
        await client.admin.command("ping")
        logger.info("Pinged your deployment. You successfully connected to MongoDB!")

        return client
    except Exception:
        logger.exception("Failed to connect to the database")
        raise


async def connect_redis(redis_config: RedisConfig) -> Redis:
    redis_client = Redis(
        host=redis_config.host,
        port=redis_config.port,
        decode_responses=True,
        username=redis_config.username,
        password=redis_config.password,
    )

    try:
        await redis_client.ping()
        logger.info("Pinged redis server. You successfully connected to redis!")

        return redis_client
    except:
        logger.exception("Failed to connect to redis")
        raise
