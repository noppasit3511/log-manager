# การติดตั้งแบบ SaaS (Public Cloud Deployment)
เอกสารนี้อธิบายขั้นตอนการนำระบบ Mini SIEM ขึ้นรันบน Public Cloud เพื่อให้บริการในรูปแบบ Software as a Service (SaaS) โดยรองรับการเชื่อมต่อผ่าน HTTPS (TLS)

## สถาปัตยกรรม Cloud ที่ใช้
- **Database:** PostgreSQL Hosted on Render.com (Singapore Region)
- **Backend API:** Web Service on Render.com (Python FastAPI)
- **Frontend UI:** Static Hosting on Vercel.com (HTML/JS)

## ขั้นตอนการติดตั้ง (Deployment Steps)

### 1. Database Setup (Render)
1. สร้าง **PostgreSQL** บนเว็บ Render.com
2. คัดลอก `External Database URL` เตรียมไว้สำหรับเชื่อมต่อกับ Backend

### 2. Backend API Setup (Render)
1. สร้าง **Web Service** บนเว็บ Render.com โดยเชื่อมต่อกับ GitHub Repository ของโปรเจกต์
2. ตั้งค่า Environment ดังนี้:
   - `Build Command`: `pip install -r backend/requirements.txt`
   - `Start Command`: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
3. เพิ่ม Environment Variable:
   - `DATABASE_URL`: นำ URL จากขั้นตอนที่ 1 มาใส่
4. รอจนกระทั่งระบบ Deploy สำเร็จ และจดจำ URL ของ API ไว้ (เช่น `https://your-api.onrender.com`)

### 3. Frontend Setup (Vercel)
1. แก้ไขไฟล์ `frontend/index.html` โดยเปลี่ยนค่าตัวแปร `API_URL` ให้ชี้ไปยัง URL ของ Backend ที่ได้จากขั้นตอนที่ 2
2. นำโฟลเดอร์ `frontend` หรือไฟล์ `index.html` ขึ้นโฮสต์ที่ Vercel.com
3. ระบบพร้อมใช้งานผ่าน URL ของ Vercel (รองรับ HTTPS อัตโนมัติ)

## การทดสอบการใช้งาน (Acceptance Testing)
- **Ingest API:** สามารถส่งข้อมูลผ่านโปรแกรม Postman ด้วยเมธอด `POST` ไปที่ `https://<api-url>/ingest`
- **Dashboard:** เปิดหน้าเว็บผ่าน Vercel และทดลองเปลี่ยนสิทธิ์การเข้าถึงผ่าน Dropdown เมนูเพื่อทดสอบระบบ Multi-tenant (RBAC)