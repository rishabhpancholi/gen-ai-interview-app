from fastapi import APIRouter, Depends, Body, Request, Response, status
from redis.asyncio import Redis
from pymongo.asynchronous.database import AsyncDatabase
from utils import get_db, get_redis
from models import CreateUser, LoginUser
from services import signup, login, blacklist_token

auth_router = APIRouter(tags=["Authentication"])


@auth_router.post(
    "/signup",
    description="""Register a new user\n
    Expects name, email and password in the request body""",
    status_code=status.HTTP_201_CREATED,
)
async def signup_handler(
    resp: Response, input: CreateUser = Body(...), db: AsyncDatabase = Depends(get_db)
) -> None:
    """
    Registers a new user\n
    Expects name, email and password in the request body
    """
    access_token = await signup(input, db)

    resp.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
    )


@auth_router.post(
    "/login",
    description="""Logs in a user\n
    Expects email and password in the request body""",
)
async def login_handler(
    resp: Response, input: LoginUser = Body(...), db: AsyncDatabase = Depends(get_db)
) -> None:
    """
    Logs in a user\n
    Expects email and password in the request body"""
    access_token = await login(input, db)

    print(access_token)

    resp.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
    )


@auth_router.post(
    "/logout", description="Logs out a user and blacklists the access token"
)
async def logout_handler(
    req: Request, resp: Response, redis: Redis = Depends(get_redis)
) -> None:
    """Logs out a user and blacklists the access token"""
    access_token = req.cookies.get("access_token")
    if not access_token:
        return

    await blacklist_token(access_token, redis)

    resp.delete_cookie(key="access_token", httponly=True, secure=False, samesite="lax")
