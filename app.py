import logging
from langchain_groq import ChatGroq
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from core import api_config, redis_config, Clients
from clients import connect_db, connect_redis
from contextlib import asynccontextmanager
from routes import auth_router

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_client = await connect_db(api_config.mongo_db_uri)
    redis_client = await connect_redis(redis_config)
    llm = ChatGroq(model=api_config.groq_model, api_key=api_config.groq_api_key)
    app.state.clients = Clients(db_client=db_client, redis_client=redis_client, llm=llm)
    yield

    logger.info("Closing connection with MongoDB!")
    await db_client.aclose()
    logger.info("Closing connection with Redis!")
    await redis_client.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(req: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Something went wrong"},
    )


routers = [auth_router]
for router in routers:
    app.include_router(router)
