from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
from pathlib import Path

class Settings(BaseSettings):
    # LLM Settings
    groq_api_key: str = ""
    gemini_api_key: str = "AIzaSyBJLHz_lNhtScBXfQbfz0rHJbtXMM2COUg"
    llm_model: str = "llama-3.3-70b-versatile"

    # Database
    database_url: str = "sqlite+aiosqlite:///./appointments.db"
    sync_database_url: str = "sqlite:///./appointments.db"
    mongo_uri: Optional[str] = "mongodb+srv://syedalikamal5:OlHOXx2YVNqHoYQX@ai-cafebot.cwfw1oc.mongodb.net/?retryWrites=true&w=majority&appName=AI-CAFEBOT"
    db_name: str = "AI-CAFEBOT"

    # Google Calendar
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"
    google_refresh_token: Optional[str] = None
    google_calendar_id: str = "primary"

    # App Settings
    secret_key: str = "super_secret_cafe_appointment_key"
    app_name: str = "Fireball Cafe & Appointment Bot"
    company_name: str = "Fireball Cafe & Bistro"
    port: int = 8000
    environment: str = "development"
    frontend_url: str = "http://localhost:3000"
    session_expiry_hours: int = 24

    class Config:
        env_file = str(Path(__file__).resolve().parents[3] / ".env")
        extra = "ignore"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()
