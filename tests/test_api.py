import pytest
from fastapi.testclient import TestClient
import sys
import os

# ตั้งค่า Path ให้หาโฟลเดอร์ backend เจอ
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from main import app

client = TestClient(app)

def test_root_endpoint():
    """Test Case 1: เช็คว่า API รันขึ้นและตอบสนองปกติไหม"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Log Management System Ready!"}

def test_ingest_log():
    """Test Case 2: จำลองการยิง Log (POST) เข้าสู่ระบบ"""
    payload = {
        "source": "pytest",
        "level": "INFO",
        "message": "This is a test log from pytest",
        "data": {
            "tenant": "demoA",
            "src_ip": "192.168.1.100",
            "action": "login"
        }
    }
    response = client.post("/ingest", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["tenant"] == "demoA"

def test_get_logs_unauthorized():
    """Test Case 3: ทดสอบระบบรักษาความปลอดภัย (ถ้าไม่ใส่ X-API-Key ต้องโดนบล็อก 401)"""
    response = client.get("/logs")
    assert response.status_code == 401
    assert "Missing X-API-Key" in response.json()["detail"]

def test_get_logs_authorized():
    """Test Case 4: ทดสอบระบบ RBAC (ใส่ Key ของ Admin ต้องดึงข้อมูลได้สำเร็จ)"""
    response = client.get("/logs", headers={"X-API-Key": "admin-key"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)