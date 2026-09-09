from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Any
from datetime import date, time

class ChatRequest(BaseModel):
    session_id: str
    message: str

    @field_validator("session_id")
    @classmethod
    def session_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("session_id cannot be empty")
        return v.strip()[:64]

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()[:2000]

class ServiceSchema(BaseModel):
    id: str
    name: str
    description: str
    duration_minutes: int
    is_active: bool

class ChatResponse(BaseModel):
    reply: str
    state: str = "GREET"
    collected_data: dict = {}
    show_services: bool = False
    services: List[ServiceSchema] = []
    booking_id: Optional[str] = None
    meet_link: Optional[str] = None
    cart_items: list = []
    has_receipt: bool = False

class BookingCreateRequest(BaseModel):
    service_name: str
    customer_name: str
    customer_email: EmailStr
    appointment_date: date
    appointment_time: time
    notes: Optional[str] = None

class BookingResponse(BaseModel):
    id: str
    service_id: str
    service_name: Optional[str] = None
    customer_name: str
    customer_email: str
    appointment_date: str
    appointment_time: str
    status: str
    calendar_event_id: Optional[str] = None
    meet_link: Optional[str] = None
    notes: Optional[str] = None
    created_at: str

class ConfirmBookingRequest(BaseModel):
    session_id: str

class ServiceCreateRequest(BaseModel):
    name: str
    description: str
    duration_minutes: int

class CustomerCredentials(BaseModel):
    customer_name: str
    customer_phone: str
    session_id: str
