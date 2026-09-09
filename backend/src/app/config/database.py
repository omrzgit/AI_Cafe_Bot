from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config.settings import get_settings
from pathlib import Path

settings = get_settings()

_BASE_DIR = Path(__file__).resolve().parents[3]

def _resolve_db_url(url: str) -> str:
    """Convert relative sqlite path to absolute based on project root."""
    if url.startswith("sqlite") and "///./" in url:
        db_file = url.split("///./")[1]
        return url.replace("///./", f"///{_BASE_DIR}/")
    return url

def _make_engine_kwargs() -> dict:
    """Return engine kwargs appropriate for the DB backend."""
    url = settings.database_url
    if url.startswith("sqlite"):
        return {"echo": settings.environment == "development", "pool_pre_ping": True}
    return {
        "echo": settings.environment == "development",
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
    }

resolved_url = _resolve_db_url(settings.database_url)
engine = create_async_engine(resolved_url, **_make_engine_kwargs())

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Create all tables and seed initial data."""
    async with engine.begin() as conn:
        from app.models import booking, service, session
        await conn.run_sync(Base.metadata.create_all)
