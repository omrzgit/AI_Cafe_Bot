from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.service import Service

class ServicesCatalog:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_active(self) -> list[Service]:
        result = await self.db.execute(
            select(Service).where(Service.is_active == True).order_by(Service.name)  # noqa: E712
        )
        return result.scalars().all()

    async def seed_default_services(self):
        """Seed default cafe reservation and booking services if none exist."""
        result = await self.db.execute(select(Service))
        existing = result.scalars().first()
        if existing:
            return

        defaults = [
            Service(
                name="Table Reservation",
                description="60-minute table reservation for dine-in meals, family gatherings, and friends.",
                duration_minutes=60,
            ),
            Service(
                name="Coffee & Burger Tasting Experience",
                description="45-minute curated gourmet burger pairing and artisanal espresso tasting session.",
                duration_minutes=45,
            ),
            Service(
                name="Barista Masterclass & Brewing",
                description="60-minute hands-on specialty coffee brewing and latte art coaching workshop.",
                duration_minutes=60,
            ),
            Service(
                name="Event & Catering Consultation",
                description="30-minute consultation call to plan custom party platters, birthdays, and private events.",
                duration_minutes=30,
            ),
        ]
        for svc in defaults:
            self.db.add(svc)
        await self.db.flush()
