from fastapi import HTTPException, status
from redis.asyncio import Redis
from models import CreateUser, LoginUser
from pymongo.asynchronous.database import AsyncDatabase
from utils import hash_password, verify_password, create_access_token
from datetime import datetime

REDIS_EXPIRE_TIME = 1800


async def signup(input: CreateUser, db: AsyncDatabase) -> str:
    """Registers a new user in db and returns an access token"""
    collection = db.get_collection("users")
    existing_user: dict = await collection.find_one({"email": input.email})

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists with this email",
        )

    hashed_pw = hash_password(input.password)
    input.password = hashed_pw

    result = await collection.insert_one(
        {**input.model_dump(), "created_at": datetime.now()}
    )

    access_token = create_access_token(
        {**input.model_dump(exclude={"password"}), "id": str(result.inserted_id)}
    )
    return access_token


async def login(input: LoginUser, db: AsyncDatabase) -> str:
    """Logs in a user and returns an access token"""
    collection = db.get_collection("users")
    existing_user: dict = await collection.find_one({"email": input.email})

    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist",
        )

    if not verify_password(input.password, existing_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    access_token = create_access_token(
        {
            "id": str(existing_user["_id"]),
            "name": existing_user["name"],
            "email": existing_user["email"],
        }
    )

    return access_token


async def blacklist_token(access_token: str, redis: Redis) -> None:
    """Blacklists an access token in redis"""
    await redis.setex(access_token, REDIS_EXPIRE_TIME, "blacklisted")
