import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config.settings import get_settings
from app.config.database import init_db
from app.middleware.logging_middleware import request_logging_middleware
from app.routes.chat import router as chat_router
from app.routes.services_bookings import router as services_bookings_router
from app.routes.cafe import router as cafe_router

settings = get_settings()

logging.basicConfig(
    level=logging.DEBUG if settings.environment == "development" else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("?? Starting up ? initialising database & catalog ...")
    await init_db()

    from app.config.database import AsyncSessionLocal
    from app.services.services.catalog_service import ServicesCatalog
    async with AsyncSessionLocal() as db:
        catalog = ServicesCatalog(db)
        await catalog.seed_default_services()
        await db.commit()

    logger.info("? Database & Service Catalog ready")
    logger.info(f"?? LLM Model: {settings.llm_model}")
    logger.info(f"?? CORS Origin: {settings.frontend_url}")
    yield
    logger.info("?? Shutting down ...")

app = FastAPI(
    title=settings.app_name,
    description="AI Cafe & Appointment Booking Assistant ? FastAPI, LangGraph, Groq, Gemini & Google Calendar",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.middleware("http")(request_logging_middleware)

# Register routes
app.include_router(chat_router)
app.include_router(services_bookings_router)
app.include_router(cafe_router)

@app.get("/", tags=["health"])
def root():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": "2.0.0",
        "message": "AI Cafe & Appointment Booking Backend is online.",
        "docs": "/docs"
    }

@app.get("/api/health", tags=["health"])
async def health():
    return {
        "status": "ok",
        "model": settings.llm_model,
        "provider": "Groq / Gemini",
        "framework": "FastAPI + LangGraph + LangChain",
        "environment": settings.environment,
    }

@app.get("/auth/google", tags=["auth"])
async def google_oauth_start():
    """Start Google OAuth2 flow for Calendar & Meet integration."""
    try:
        from google_auth_oauthlib.flow import Flow
        flow = Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uris": [settings.google_redirect_uri],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=["https://www.googleapis.com/auth/calendar"],
        )
        flow.redirect_uri = settings.google_redirect_uri
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        from fastapi.responses import RedirectResponse
        return RedirectResponse(auth_url)
    except Exception as e:
        logger.error(f"Google OAuth start error: {e}")
        return {"error": str(e)}

@app.get("/auth/google/callback", tags=["auth"])
async def google_oauth_callback(code: str):
    """Callback to receive the Google refresh token."""
    try:
        from google_auth_oauthlib.flow import Flow
        flow = Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uris": [settings.google_redirect_uri],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=["https://www.googleapis.com/auth/calendar"],
        )
        flow.redirect_uri = settings.google_redirect_uri
        flow.fetch_token(code=code)
        refresh_token = flow.credentials.refresh_token
        logger.info(f"? Google refresh token obtained: {refresh_token}")
        return {
            "message": "Google Calendar connected successfully!",
            "refresh_token": refresh_token,
            "instruction": "Set GOOGLE_REFRESH_TOKEN in your .env file and restart server.",
        }
    except Exception as e:
        logger.error(f"Google OAuth error: {e}")
        return {"error": str(e)}
