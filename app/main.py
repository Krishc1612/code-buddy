from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.routes import auth
from app.db.database import create_db_and_tables
from app.api.routes import chats

@asynccontextmanager
async def lifespan(app : FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(
    title = "Code-buddy API",
    version = "1.0.0",
    lifespan = lifespan
)

app.include_router(auth.router, prefix = "/api", tags = ["auth"])
app.include_router(chats.router, prefix = "/api", tags = ['chats'])

@app.get('/')
async def root():
    return {
        "status" : "Code-budy API running"
    }