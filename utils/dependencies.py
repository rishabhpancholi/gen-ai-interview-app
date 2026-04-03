from pymongo import AsyncMongoClient
from redis.asyncio import Redis
from pymongo.asynchronous.database import AsyncDatabase
from core import api_config
from fastapi import Request, Depends, HTTPException, status
from jose import jwt, ExpiredSignatureError, JWTError

SECRET_KEY = api_config.jwt_secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def get_db(req: Request):
    client: AsyncMongoClient = req.app.state.db_client
    db: AsyncDatabase = client.get_database(api_config.mongo_db_database_name)
    yield db


def get_redis(req: Request):
    redis_client: Redis = req.app.state.redis_client
    yield redis_client


def authorize_user(req: Request, redis: Redis = Depends(get_redis)) -> dict:
    auth_header = req.headers.get("Authorization")

    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )

    parts = auth_header.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )

    access_token = parts[1]

    if redis.get(access_token) == "blacklisted":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    try:
        user = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
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
