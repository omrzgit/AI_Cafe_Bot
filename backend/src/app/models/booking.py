import uuid
from datetime import datetime, date, time
from sqlalchemy import String, Date, Time, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.config.database import Base

class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    service_id: Mapped[str] = mapped_column(String(36), ForeignKey("services.id"), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(200), nullable=False)
    appointment_date: Mapped[date] = mapped_column(Date, nullable=False)
    appointment_time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    calendar_event_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    meet_link: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    service: Mapped["Service"] = relationship("Service", back_populates="bookings")

    def to_dict(self):
        created_str = self.created_at.isoformat() if self.created_at else datetime.utcnow().isoformat()
        date_str = self.appointment_date.isoformat() if hasattr(self.appointment_date, "isoformat") else str(self.appointment_date)
        time_str = self.appointment_time.strftime("%H:%M") if hasattr(self.appointment_time, "strftime") else str(self.appointment_time)[:5]
        return {
            "id": self.id or str(uuid.uuid4()),
            "service_id": self.service_id,
            "service_name": self.service.name if self.service else None,
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
            "appointment_date": date_str,
            "appointment_time": time_str,
            "status": self.status or "pending",
            "calendar_event_id": self.calendar_event_id,
            "meet_link": self.meet_link,
            "notes": self.notes,
            "created_at": created_str,
        }
