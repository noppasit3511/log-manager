import requests
import json
import time
import random
from datetime import datetime

API_URL = "http://localhost:8000/ingest"

def send_log(source, level, message, data):
    payload = {
        "source": source,
        "level": level,
        "message": message,
        "data": data
    }
    try:
        response = requests.post(API_URL, json=payload)
        status = response.status_code
        if status == 200:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 📤 Sent {source:15} -> 📥 Status: {status} (Success)")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Failed {source:15} -> Status: {status}")
    except requests.exceptions.ConnectionError:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Connection Error: ไม่สามารถเชื่อมต่อ API ได้ (เช็คว่า Docker รันอยู่ไหม?)")

# 1. จำลอง AWS CloudTrail (Cloud Source)
def mock_aws_log():
    data = {
        "tenant": "demoA",  # กำหนด Tenant ให้ demoA
        "event_source": "iam.amazonaws.com",
        "eventName": "CreateUser", # ตั้งใจใช้ eventName เพื่อทดสอบ Normalization
        "user_identity": "admin-root",
        "source_ip": f"54.239.25.{random.randint(1, 255)}", 
        "region": "us-east-1"
    }
    send_log("AWS_CloudTrail", "INFO", "IAM User created successfully", data)

# 2. จำลอง CrowdStrike (Endpoint Security)
def mock_crowdstrike_log():
    data = {
        "tenant": "demoB", # กำหนด Tenant ให้ demoB
        "event_type": "MalwareDetected",
        "severity": 8,
        "file_name": "malware.exe",
        "ip": f"10.0.0.{random.randint(1, 255)}",
        "action": "Quarantined"
    }
    send_log("CrowdStrike", "ERROR", "Malicious file detected on WIN10-PRO", data)

# 3. จำลอง Microsoft 365 (SaaS Source)
def mock_m365_log():
    data = {
        "tenant": "demoA", # กำหนด Tenant ให้ demoA
        "workload": "Exchange",
        "username": "bob@demo.local", # ตั้งใจใช้ username ทดสอบ Normalization
        "client_ip": f"198.51.100.{random.randint(1, 255)}",
        "status": "Success"
    }
    send_log("M365_Audit", "INFO", "User logged into Outlook Web", data)

# 4. จำลอง Windows AD (Internal Auth)
def mock_ad_log():
    data = {
        "tenant": "demoB", # กำหนด Tenant ให้ demoB
        "event_id": 4625,
        "logon_type": 3,
        "source_address": f"203.0.113.{random.randint(1, 255)}",
        "user": "Guest_Account",
        "reason": "bad_password"
    }
    send_log("ActiveDirectory", "WARNING", "Failed Logon attempt", data)

# ==========================================
# ส่วนนี้คือไกปืนที่ขาดหายไป! (คำสั่งเรียกใช้ฟังก์ชัน)
# ==========================================
if __name__ == "__main__":
    print("🚀 เริ่มจำลองการยิง Log 4 แหล่ง... (กด Ctrl+C เพื่อหยุด)")
    print("-" * 50)
    
    # รวบรวมฟังก์ชันไว้ในลิสต์
    log_functions = [mock_aws_log, mock_crowdstrike_log, mock_m365_log, mock_ad_log]
    
    try:
        while True:
            # สุ่มเรียกฟังก์ชัน 1 อันจาก 4 แหล่ง
            random_func = random.choice(log_functions)
            random_func()
            
            # สุ่มหน่วงเวลา 1-3 วินาที จะได้ดูกราฟไหลเป็นธรรมชาติ
            time.sleep(random.uniform(1, 3))
            
    except KeyboardInterrupt:
        print("\n🛑 หยุดการจำลอง Log เรียบร้อยแล้ว")