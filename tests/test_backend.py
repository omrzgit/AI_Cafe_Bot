import pytest
import os
import sys
from datetime import date, time
from pathlib import Path

# Add backend/src to sys.path
backend_src = str(Path(__file__).resolve().parents[1] / "backend" / "src")
if backend_src not in sys.path:
    sys.path.insert(0, backend_src)

from app.utils.date_utils import parse_date, parse_time
from app.models.service import Service
from app.models.booking import Booking
from app.services.ai.nodes import validate_output
from app.services.ai.prompts import build_prompt

def test_date_utils():
    d = parse_date("2026-10-15")
    assert str(d) == "2026-10-15"
    t = parse_time("14:30")
    assert str(t) == "14:30:00"

def test_service_model():
    svc = Service(
        name="Test Table Reservation",
        description="Reserve a luxury table",
        duration_minutes=60,
    )
    d = svc.to_dict()
    assert d["name"] == "Test Table Reservation"
    assert d["duration_minutes"] == 60
    assert d["is_active"] is True

def test_booking_model():
    d_obj = parse_date("2026-11-20")
    t_obj = parse_time("15:00")
    b = Booking(
        service_id="test-svc-123",
        customer_name="John Doe",
        customer_email="john@example.com",
        appointment_date=d_obj,
        appointment_time=t_obj,
        status="confirmed"
    )
    d = b.to_dict()
    assert d["customer_name"] == "John Doe"
    assert d["customer_email"] == "john@example.com"
    assert d["appointment_date"] == "2026-11-20"
    assert d["appointment_time"] == "15:00"
    assert d["status"] == "confirmed"

def test_validation_node_date_and_email():
    state = {
        "current_state": "COLLECT_DETAILS",
        "next_state": "COLLECT_DETAILS",
        "collected_data": {"service": "Table Reservation"},
        "extracted": {
            "name": "Jane Doe",
            "email": "invalid_email_no_at",
            "date": "2020-01-01",  # Past date
            "time": "18:00"
        }
    }
    result = validate_output(state)
    assert "date" not in result["collected_data"]
    assert "email" not in result["collected_data"]
    assert result["collected_data"]["name"] == "Jane Doe"
    assert result["collected_data"]["time"] == "18:00"

def test_validation_node_complete_transitions_to_confirm():
    state = {
        "current_state": "COLLECT_DETAILS",
        "next_state": "COLLECT_DETAILS",
        "collected_data": {},
        "extracted": {
            "service": "Table Reservation",
            "name": "Jane Doe",
            "email": "jane@example.com",
            "date": "2026-12-25",
            "time": "19:00"
        }
    }
    result = validate_output(state)
    assert result["current_state"] == "CONFIRM"
    assert result["collected_data"]["service"] == "Table Reservation"

def test_prompt_builder():
    services = [
        {"name": "Table Reservation", "duration_minutes": 60, "description": "Dine in"}
    ]
    prompt = build_prompt(
        current_state="GREET",
        collected_data={},
        services=services,
        company_name="Fireball Cafe"
    )
    assert prompt is not None
