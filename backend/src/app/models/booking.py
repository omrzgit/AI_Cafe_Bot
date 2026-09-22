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
        return {
            "id": self.id,
            "service_id": self.service_id,
            "service_name": self.service.name if self.service else None,
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
            "appointment_date": self.appointment_date.isoformat(),
            "appointment_time": self.appointment_time.strftime("%H:%M"),
            "status": self.status,
            "calendar_event_id": self.calendar_event_id,
            "meet_link": self.meet_link,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
        }
