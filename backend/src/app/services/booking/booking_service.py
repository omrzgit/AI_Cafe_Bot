import logging
from datetime import date, time, datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload

from app.models.booking import Booking
from app.models.service import Service
from app.services.calendar.google_calendar import CalendarService, CalendarNotConfiguredError

logger = logging.getLogger(__name__)

class BookingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.calendar = CalendarService()

    async def create_booking(
        self,
        service_name: str,
        customer_name: str,
        customer_email: str,
        appointment_date: date,
        appointment_time: time,
        notes: Optional[str] = None,
    ) -> Booking:
        result = await self.db.execute(
            select(Service).where(
                and_(Service.name == service_name, Service.is_active == True)  # noqa: E712
            )
        )
        service = result.scalar_one_or_none()

        if not service:
            result = await self.db.execute(
                select(Service).where(Service.is_active == True)
            )
            all_services = result.scalars().all()
            service = next(
                (s for s in all_services if service_name.lower() in s.name.lower()),
                None,
            )
            if not service:
                raise ValueError(f"Service '{service_name}' not found")

        if await self.check_conflict(service.id, appointment_date, appointment_time):
            raise ValueError(
                f"The slot {appointment_date} at {appointment_time.strftime('%H:%M')} "
                "is already taken. Please choose a different time."
            )

        booking = Booking(
            service_id=service.id,
            customer_name=customer_name,
            customer_email=customer_email,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            status="pending",
            notes=notes,
        )
        self.db.add(booking)
        await self.db.flush()

        from app.config.settings import get_settings
        company = get_settings().company_name

        try:
            event_result = await self.calendar.create_event(
                summary=f"{service.name} - {customer_name}",
                description=f"Booked via {company} AI assistant",
                start_datetime=datetime.combine(appointment_date, appointment_time),
                duration_minutes=service.duration_minutes,
                attendee_email=customer_email,
                timezone="Asia/Kolkata",
            )
            booking.calendar_event_id = event_result.get("id")
            booking.meet_link = event_result.get("meet_link")
            booking.status = "confirmed"
            logger.info(f"Calendar event created: {event_result.get('id')}")
        except CalendarNotConfiguredError:
            logger.info("Google Calendar not configured ? booking saved without calendar event")
            booking.status = "confirmed"
        except Exception as e:
            logger.warning(
                f"Google Calendar event creation failed: {e}. "
                "Booking saved with status=pending_calendar for retry."
            )
            booking.status = "pending_calendar"

        await self.db.flush()
        return booking

    async def check_conflict(
        self, service_id: str, appointment_date: date, appointment_time: time
    ) -> bool:
        result = await self.db.execute(
            select(Booking).where(
                and_(
                    Booking.service_id == service_id,
                    Booking.appointment_date == appointment_date,
                    Booking.appointment_time == appointment_time,
                    Booking.status.in_(["pending", "confirmed", "pending_calendar"]),
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_booking(self, booking_id: str) -> Optional[Booking]:
        result = await self.db.execute(
            select(Booking)
            .options(joinedload(Booking.service))
            .where(Booking.id == booking_id)
        )
        return result.scalar_one_or_none()

    async def get_bookings_by_email(self, email: str) -> list[Booking]:
        result = await self.db.execute(
            select(Booking)
            .options(joinedload(Booking.service))
            .where(Booking.customer_email == email)
            .order_by(Booking.appointment_date.desc())
        )
        return result.scalars().all()

    async def cancel_booking(self, booking_id: str) -> Booking:
        result = await self.db.execute(
            select(Booking)
            .options(joinedload(Booking.service))
            .where(Booking.id == booking_id)
        )
        booking = result.scalar_one_or_none()
        if not booking:
            raise ValueError("Booking not found")

        if booking.calendar_event_id:
            try:
                await self.calendar.delete_event(booking.calendar_event_id)
            except Exception as e:
                logger.warning(f"Failed to delete calendar event {booking.calendar_event_id}: {e}")

        booking.status = "cancelled"
        await self.db.flush()
        return booking
