import logging
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config.settings import get_settings
from app.models.session import ChatSession
from app.models.service import Service
from app.services.ai.booking_graph import booking_graph

logger = logging.getLogger(__name__)
settings = get_settings()

class AIOrchestrator:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_message(self, session_id: str, user_message: str) -> dict:
        session = await self._get_or_create_session(session_id)

        expiry_threshold = datetime.utcnow() - timedelta(hours=settings.session_expiry_hours)
        if session.updated_at < expiry_threshold:
            logger.info(f"Session {session_id} expired ? resetting to GREET")
            session.state = "GREET"
            session.collected_data = {}
            session.messages = []

        services = await self._get_active_services()

        initial_state = {
            "session_id": session_id,
            "user_message": user_message,
            "messages": list(session.messages or []),
            "current_state": session.state,
            "next_state": session.state,
            "reply": "",
            "extracted": {},
            "collected_data": dict(session.collected_data or {}),
            "services": services,
            "company_name": settings.company_name,
            "show_services": False,
            "error": None,
        }

        result_state = await booking_graph.ainvoke(initial_state)

        reply         = result_state.get("reply", "Could you please repeat that?")
        new_state     = result_state.get("current_state", session.state)
        collected     = result_state.get("collected_data", session.collected_data or {})
        show_services = result_state.get("show_services", False)

        trimmed_messages = result_state.get("_trimmed_messages")
        if trimmed_messages is not None:
            updated_messages = trimmed_messages
        else:
            updated_messages = result_state.get("messages", [])[-20:]

        session.state          = new_state
        session.collected_data = {} if new_state == "BOOKED" else collected
        session.messages       = updated_messages
        session.updated_at     = datetime.utcnow()
        await self.db.flush()

        return {
            "reply": reply,
            "state": new_state,
            "collected_data": collected,
            "show_services": show_services,
            "services": services if show_services else [],
        }

    async def _get_or_create_session(self, session_id: str) -> ChatSession:
        result = await self.db.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            session = ChatSession(
                session_id=session_id,
                state="GREET",
                collected_data={},
                messages=[],
            )
            self.db.add(session)
            await self.db.flush()

        return session

    async def _get_active_services(self) -> list[dict]:
        result = await self.db.execute(
            select(Service).where(Service.is_active == True)  # noqa: E712
        )
        return [s.to_dict() for s in result.scalars().all()]
