from fastapi import HTTPException, status
from redis.asyncio import Redis
from models import CreateUser, LoginUser
from pymongo.asynchronous.database import AsyncDatabase
from utils import hash_password, verify_password, create_access_token
from pymongo.errors import DuplicateKeyError
from datetime import datetime, timezone
from core import api_config


async def signup(input: CreateUser, db: AsyncDatabase) -> str:
    """Registers a new user in db and returns an access token"""
    collection = db.get_collection("users")

    input_data: dict = input.model_dump()

    hashed_pw = hash_password(input_data["password"])
    input_data["password"] = hashed_pw

    try:
        result = await collection.insert_one(
            {**input_data, "created_at": datetime.now(timezone.utc)}
        )
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    access_token = create_access_token(
        {
            "email": input_data["email"],
            "id": str(result.inserted_id),
        }
    )
    return access_token


async def login(input: LoginUser, db: AsyncDatabase) -> str:
    """Logs in a user and returns an access token"""
    collection = db.get_collection("users")
    fake_hash = api_config.fake_hash
    existing_user: dict = await collection.find_one({"email": input.email})

    hashed = existing_user.get("password") if existing_user else fake_hash

    if not verify_password(input.password, hashed):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    access_token = create_access_token(
        {
            "id": str(existing_user["_id"]),
            "email": existing_user["email"],
        }
    )

    return access_token


async def blacklist_token(access_token: str, redis: Redis) -> None:
    """Blacklists an access token in redis"""
    await redis.setex(
        access_token, api_config.access_token_expire_minutes * 60, "blacklisted"
    )
