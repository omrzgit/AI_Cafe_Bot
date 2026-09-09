import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.models.service import Service
from app.routes.schemas import (
    ServiceSchema,
    ServiceCreateRequest,
    BookingCreateRequest,
    BookingResponse,
)
from app.services.booking.booking_service import BookingService
from app.services.services.catalog_service import ServicesCatalog

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["services & bookings"])

@router.get("/services", response_model=list[ServiceSchema])
async def list_services(db: AsyncSession = Depends(get_db)):
    """Return all active appointment services."""
    catalog = ServicesCatalog(db)
    services = await catalog.get_all_active()
    return [s.to_dict() for s in services]

@router.post("/services", response_model=ServiceSchema, status_code=201)
async def create_service(
    payload: ServiceCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new service (admin use)."""
    service = Service(
        name=payload.name,
        description=payload.description,
        duration_minutes=payload.duration_minutes,
    )
    db.add(service)
    await db.flush()
    await db.commit()
    return service.to_dict()

@router.post("/bookings", response_model=BookingResponse, status_code=201)
async def create_booking(
    payload: BookingCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Directly create a booking (bypasses the chat flow)."""
    try:
        svc = BookingService(db)
        booking = await svc.create_booking(
            service_name=payload.service_name,
            customer_name=payload.customer_name,
            customer_email=str(payload.customer_email),
            appointment_date=payload.appointment_date,
            appointment_time=payload.appointment_time,
            notes=payload.notes,
        )
        await db.commit()
        return booking.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Booking creation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not create booking")

@router.get("/bookings/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve a single booking by ID."""
    svc = BookingService(db)
    booking = await svc.get_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking.to_dict()

@router.get("/bookings", response_model=list[BookingResponse])
async def list_bookings_by_email(
    email: str = Query(..., description="Customer email address"),
    db: AsyncSession = Depends(get_db),
):
    """List all bookings for a given customer email."""
    svc = BookingService(db)
    bookings = await svc.get_bookings_by_email(email)
    return [b.to_dict() for b in bookings]

@router.delete("/bookings/{booking_id}", response_model=BookingResponse)
async def cancel_booking(booking_id: str, db: AsyncSession = Depends(get_db)):
    """Cancel a booking and remove the corresponding calendar event."""
    try:
        svc = BookingService(db)
        booking = await svc.cancel_booking(booking_id)
        await db.commit()
        return booking.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Cancel booking error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not cancel booking")
