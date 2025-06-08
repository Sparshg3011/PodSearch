from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import youtube

app = FastAPI(
    title="PodPilot Backend API",
    description="API for podcast search, transcription, and querying",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(youtube.router, prefix="/search", tags=["Search"])

@app.get("/")
async def root():
    return {"message": "PodPilot Backend API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}