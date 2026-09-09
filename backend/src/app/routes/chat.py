import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.routes.schemas import ChatRequest, ChatResponse
from app.services.ai.orchestrator import AIOrchestrator
from app.services.booking.booking_service import BookingService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    try:
        orchestrator = AIOrchestrator(db)
        result = await orchestrator.process_message(
            session_id=request.session_id,
            user_message=request.message,
        )
    except Exception as e:
        logger.error(f"Orchestrator error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal AI processing error: {e}")

    if result["state"] == "BOOKED" and result["collected_data"].get("name"):
        collected = result["collected_data"]

        if not result.get("booking_id"):
            try:
                booking_service = BookingService(db)
                booking = await booking_service.create_booking(
                    service_name=collected["service"],
                    customer_name=collected["name"],
                    customer_email=collected["email"],
                    appointment_date=datetime.strptime(collected["date"], "%Y-%m-%d").date(),
                    appointment_time=datetime.strptime(collected["time"], "%H:%M").time(),
                )
                result["booking_id"] = booking.id
                result["meet_link"] = booking.meet_link
                logger.info(f"Booking created: {booking.id} for session {request.session_id}")
            except ValueError as e:
                logger.warning(f"Booking creation failed: {e}")
                result["state"] = "COLLECT_DETAILS"
                result["reply"] = f"?? {str(e)} Please provide a different date or time."
            except Exception as e:
                logger.error(f"Unexpected booking error: {e}", exc_info=True)
                result["reply"] += (
                    "\n\nNote: I had trouble saving your booking details to the calendar. "
                    "Please contact our support to confirm."
                )

    return ChatResponse(**result)
