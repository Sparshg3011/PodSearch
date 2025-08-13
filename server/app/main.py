from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .api import youtube, transcripts, rag, verify
from .core.database import connect_to_mongo, close_mongo_connection

@asynccontextmanager
async def lifespan(app: FastAPI):

    try:
        await connect_to_mongo()
        print("MongoDB connection established successfully")
    except Exception as e:
        print(f"MongoDB connection failed: {e}. Some features may be limited.")
    yield
    try:
        await close_mongo_connection()
        print("MongoDB connection closed")
    except Exception as e:
        print(f"Error closing MongoDB connection: {e}")
    print("App shutdown")

app = FastAPI(
    title="PodSearch Backend API",
    description="API for podcast and video search, transcription, content querying, and fact verification with MongoDB storage",
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
app.include_router(rag.router, prefix="/api/rag", tags=["RAG"])
app.include_router(verify.router, prefix="/api/verify", tags=["Verify"])



@app.get("/")
async def root():
    return {"message": "PodPilot Backend API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}