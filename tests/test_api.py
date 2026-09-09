import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

backend_src = str(Path(__file__).resolve().parents[1] / "backend" / "src")
if backend_src not in sys.path:
    sys.path.insert(0, backend_src)

from app.main import app

def test_api_root():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "Cafe" in data["app"]

def test_api_health():
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

def test_cafe_menu():
    with TestClient(app) as client:
        response = client.get("/api/menu")
        assert response.status_code == 200
        data = response.json()
        assert "menu" in data
        assert len(data["menu"]) > 0

def test_cafe_registration_and_cart():
    with TestClient(app) as client:
        reg_payload = {
            "customer_name": "Alice Tester",
            "customer_phone": "+1 555-0100",
            "session_id": "test_sess_alice"
        }
        res_reg = client.post("/api/register", json=reg_payload)
        assert res_reg.status_code == 200
        assert res_reg.json()["success"] is True

        # Check cart
        res_cart = client.get("/api/cart/test_sess_alice")
        assert res_cart.status_code == 200
        assert res_cart.json()["customer_name"] == "Alice Tester"

def test_services_list():
    with TestClient(app) as client:
        response = client.get("/api/services")
        assert response.status_code == 200
        services = response.json()
        assert isinstance(services, list)
        assert len(services) > 0
        names = [s["name"] for s in services]
        assert "Table Reservation" in names
