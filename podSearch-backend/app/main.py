from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .api import youtube, transcripts
from .core.database import connect_to_mongo, close_mongo_connection

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield

    await close_mongo_connection()

app = FastAPI(
    title="PodSearch Backend API",
    description="API for podcast and video search, transcription, and content querying with MongoDB storage",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(youtube.router, prefix="/api/youtube", tags=["YouTube"])
app.include_router(transcripts.router, prefix="/api/transcripts", tags=["Transcripts"])


@app.get("/")
async def root():
    return {"message": "PodPilot Backend API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}