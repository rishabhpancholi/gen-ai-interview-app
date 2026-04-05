from pymongo import AsyncMongoClient
from redis.asyncio import Redis
from pymongo.asynchronous.database import AsyncDatabase
from core import api_config
from fastapi import Request, Depends, HTTPException, status
from jose import jwt, ExpiredSignatureError, JWTError


def get_db(req: Request):
    client: AsyncMongoClient = req.app.state.clients.db_client
    db: AsyncDatabase = client.get_database(api_config.mongo_db_database_name)
    yield db


def get_redis(req: Request):
    redis_client: Redis = req.app.state.clients.redis_client
    yield redis_client


def authorize_user(req: Request, redis: Redis = Depends(get_redis)) -> dict:
    access_token = req.cookies.get("access_token")

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated",
        )

    if redis.get(access_token) == "blacklisted":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    try:
        user = jwt.decode(
            access_token,
            api_config.jwt_secret_key,
            algorithms=[api_config.jwt_algorithm],
        )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired",
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token"
        )

    if not user or "email" not in user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )

    return user
