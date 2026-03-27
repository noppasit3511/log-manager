# การติดตั้งแบบ Appliance (Local / VM)
ระบบสามารถรันแบบจบในตัวบนเครื่องเดียวผ่าน Docker Compose

### ข้อกำหนดระบบ (Prerequisites)
- Docker และ Docker Compose
- Python 3.10+ (สำหรับการจำลอง Log)

### ขั้นตอนการรัน
1. Clone Repository นี้
2. เปิด Terminal ในโฟลเดอร์หลัก แล้วพิมพ์คำสั่ง:
   `make up` หรือ `docker-compose up -d --build`
3. ระบบจะเปิดพอร์ตดังนี้:
   - `8000` (TCP): FastAPI Backend
   - `514` (UDP): Syslog Ingestion
   - `5432` (TCP): PostgreSQL
4. เปิดไฟล์ `frontend/index.html` ด้วย Web Browser เพื่อดู Dashboard
5. ทดสอบส่งข้อมูลด้วยคำสั่ง `make simulate`