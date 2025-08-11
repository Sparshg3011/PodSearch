from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "PodSearch Backend API"
    VERSION: str = "1.0.0"
    YOUTUBE_MAX_RESULTS: int = 20
    
    class Config:
        env_file = ".env"

settings = Settings() 