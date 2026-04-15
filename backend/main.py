from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.routes import chats
from app.db.database import create_db_and_tables
import uvicorn
import os

from app.rag_chat.embeddings import get_embeddings
from app.rag_chat.vectorstore import get_vectorstore
from app.api.routes import auth

PORT = int(os.getenv("PORT", 2000))

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("############## Starting Code-Buddy backend ####################")

    try:
        await create_db_and_tables()
        print("\n################### Database initialized ######################\n")

        app.state.embedding_model = get_embeddings()
        print("\n######################### Embedding model loaded #######################\n")

        app.state.vectorstore = get_vectorstore()
        print("\n######################### Vectorstore loaded ############################\n")

    except Exception as e:
        print("Critical startup failure:", e)
        raise RuntimeError("Startup failed")

    yield

    print("\n######################### Shutting down... ############################\n")


app = FastAPI(
    title="Code-buddy API",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(chats.router, prefix="/api", tags=['chats'])


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT)