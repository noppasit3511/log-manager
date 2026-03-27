from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os
import asyncio
import urllib.request
import json

# 1. ตั้งค่าการเชื่อมต่อ Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password123@localhost:5432/log_db")
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1473979907267760230/BBTFwXxLUV3PdKe-b-jI1haBwAmFTTU7R4XzoBD-USPSwuHjb-Dm8UoIXiN1ZcRFmke1"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    api_key = Column(String, unique=True, index=True)
    role = Column(String)    
    tenant = Column(String)  


class LogEntry(Base):  
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    tenant = Column(String, index=True, default="general") 
    source = Column(String, index=True)
    level = Column(String, index=True)
    
    # --- ฟิลด์ที่ดึงออกมาเพื่อทำดัชนีค้นหา ---
    event_type = Column(String, index=True) 
    action = Column(String, index=True)
    src_ip = Column(String, index=True)
    user_account = Column(String, index=True)
    
    message = Column(String)
    raw_data = Column(JSONB) 

Base.metadata.create_all(bind=engine)
class LogInput(BaseModel):
    source: str
    level: str
    message: str
    data: dict = {}

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
def get_current_user(api_key: str = Security(api_key_header)):
    if not api_key:
        raise HTTPException(status_code=401, detail="Access Denied: Missing X-API-Key")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.api_key == api_key).first()
        if not user:
            raise HTTPException(status_code=403, detail="Access Denied: Invalid API Key")
        return user
    finally:
        db.close()

# Discord Alert 
def send_discord_alert(source, level, message, raw_data):
    if not DISCORD_WEBHOOK_URL:
        return
    payload = {
        "content": "**SECURITY ALERT DETECTED!**",
        "embeds": [{
            "title": f"[{source.upper()}] - {level}",
            "description": message,
            "color": 16711680,
            "fields": [
                {
                    "name": "Raw Data", 
                    "value": f"```json\n{json.dumps(raw_data, indent=2)}\n```", 
                    "inline": False
                }
            ]
        }]
    }
    try:
        req = urllib.request.Request(
            DISCORD_WEBHOOK_URL, 
            data=json.dumps(payload).encode('utf-8'), 
            headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json'}
        )
        urllib.request.urlopen(req)
        print("Sent alert to Discord successfully!")
    except Exception as e:
        print(f"Failed to send Discord alert: {e}")

# --- Data Retention ---
def cleanup_old_logs():
    db = SessionLocal()
    try:
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        deleted_count = db.query(LogEntry).filter(LogEntry.timestamp < seven_days_ago).delete()
        db.commit()
        print(f"🧹 Data Retention: ลบ Log ที่เก่ากว่า 7 วันไปจำนวน {deleted_count} รายการ")
    except Exception as e:
        print(f"Error during cleanup: {e}")
    finally:
        db.close()

# User จำลองสำหรับให้เราทดสอบ
def seed_initial_users():
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            users = [
                User(username="admin_master", api_key="admin-key", role="admin", tenant="all"),
                User(username="viewer_a", api_key="viewer-a-key", role="viewer", tenant="demoA"),
                User(username="viewer_b", api_key="viewer-b-key", role="viewer", tenant="demoB")
            ]
            db.add_all(users)
            db.commit()
            print("Seeded initial users successfully!")
    finally:
        db.close()

# --- Syslog UDP Server ---
class SyslogProtocol(asyncio.DatagramProtocol):
    def connection_made(self, transport):
        self.transport = transport
        print("Syslog UDP server listening on 0.0.0.0:5514")
    
    def datagram_received(self, data, addr):
        try:
            message = data.decode().strip()
            print(f"Received Syslog from {addr}: {message}")
            db = SessionLocal()
            try:
                new_log = LogEntry(
                    source="syslog",
                    level="INFO",
                    message=message,
                    src_ip=addr[0],
                    event_type="syslog_event",
                    raw_data={"from_ip": addr[0], "raw_message": message},
                    timestamp=datetime.utcnow()
                )
                db.add(new_log)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            print(f"Syslog Error: {e}")

# 6. รวบฟังก์ชัน Startup ให้เหลืออันเดียว
@app.on_event("startup")
async def startup_event():
    seed_initial_users()
    cleanup_old_logs()
    
    loop = asyncio.get_running_loop()
    try:
        await loop.create_datagram_endpoint(
            lambda: SyslogProtocol(),
            local_addr=('0.0.0.0', 5514)
        )
    except Exception as e:
        print(f"Cannot bind port 5514 (Need Root/Admin?): {e}")

#Ingest API + Normalization Logic
@app.post("/ingest")
def ingest_log(log: LogInput):
    db = SessionLocal()
    try:
        target_tenant = log.data.get("tenant") or "general"
        
        # --- Normalization Funnel ---
        extracted_ip = log.data.get("src_ip") or log.data.get("ip") or log.data.get("source_address") or "0.0.0.0"
        extracted_event = log.data.get("event_type") or log.data.get("eventName") or "unknown"
        extracted_user = log.data.get("user") or log.data.get("username") or "unknown"
        extracted_action = log.data.get("action") or log.data.get("status") or log.data.get("reason") or "none"

        new_log = LogEntry(
            source=log.source,
            tenant=target_tenant, 
            level=log.level.upper(), 
            event_type=extracted_event,
            action=extracted_action,
            src_ip=extracted_ip,
            user_account=extracted_user,
            message=f"[{extracted_ip}] {log.message}", 
            raw_data=log.data, 
            timestamp=datetime.utcnow()
        )

        db.add(new_log)
        db.commit()
        db.refresh(new_log)

        if log.level.upper() == "ERROR":
            send_discord_alert(log.source, log.level, log.message, log.data)

        return {"status": "success", "log_id": new_log.id, "tenant": target_tenant}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

#Search API + Role-Based Access Control (RBAC)
@app.get("/logs")
def get_logs(tenant: str = None, limit: int = 50, current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        query = db.query(LogEntry)
        
        # ถ้าเป็นแค่ Viewer บังคับให้ดูได้แค่ Tenant ตัวเอง
        if current_user.role == "viewer":
            query = query.filter(LogEntry.tenant == current_user.tenant)
        # ถ้าเป็น Admin สามารถระบุ tenant ที่อยากดูได้
        elif current_user.role == "admin" and tenant:
            query = query.filter(LogEntry.tenant == tenant)
            
        logs = query.order_by(LogEntry.timestamp.desc()).limit(limit).all()
        
        # 🚀 แปลงข้อมูลเป็น List ของ Dictionary ป้องกันบั๊ก 500 Error
        result = []
        for log in logs:
            result.append({
                "id": log.id,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "tenant": log.tenant,
                "source": log.source,
                "level": log.level,
                "event_type": log.event_type,
                "src_ip": log.src_ip,
                "message": log.message,
                "raw_data": log.raw_data
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Log Management System Ready!"}