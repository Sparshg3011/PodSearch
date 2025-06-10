from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import youtube, search, transcripts

app = FastAPI(
    title="PodSearch Backend API",
    description="API for podcast and video search, transcription, and content querying",
    version="1.0.0"
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