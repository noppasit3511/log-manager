# 🛡️ Mini SIEM - Security Log Management System

A lightweight, multi-tenant Security Information and Event Management (SIEM) system designed for centralized log ingestion, normalization, and real-time visualization.

## 🌟 Features (ความสามารถของระบบ)
ระบบนี้ถูกพัฒนาขึ้นตาม Acceptance Checklist โดยมีความสามารถดังนี้:
- **Multi-protocol Ingestion:** รองรับการรับข้อมูลทั้งแบบ Modern API (HTTP POST JSON) และ Legacy Devices (Syslog UDP 5514)
- **Data Normalization:** ระบบสามารถสกัดฟิลด์สำคัญ (IP, User, Event) และเก็บข้อมูลดิบ (Raw Data) ลงใน PostgreSQL (JSONB) เพื่อป้องกัน Data Loss
- **Multi-tenant & RBAC:** มีระบบแยกข้อมูลของลูกค้าแต่ละรายอย่างเด็ดขาด และตรวจสอบสิทธิ์ผ่าน `X-API-Key` (Admin ดูได้ทั้งหมด, Viewer ดูได้เฉพาะ Tenant ของตนเอง)
- **Real-time Dashboard:** หน้าจอ UI สำหรับดูสถิติ Top Event Sources, Timeline และค้นหาข้อมูล Log ย้อนหลัง
- **Alerting Engine:** รองรับการส่งแจ้งเตือนแบบ Real-time เข้าสู่ Discord Webhook ทันทีที่ตรวจพบ Log ระดับ `ERROR`

## 📂 Project Structure
- `/backend`: โค้ดระบบ API และ Ingestion (FastAPI, Python)
- `/frontend`: หน้าจอ Dashboard (HTML, JS, Chart.js)
- `/samples`: สคริปต์สำหรับจำลองการยิง Log เข้าระบบ (`simulate_4_sources.py`)
- `/tests`: ชุดทดสอบระบบ API (Pytest)
- `/docs`: เอกสารประกอบสถาปัตยกรรมและคู่มือการติดตั้ง

## 🚀 Deployment Guides
โปรเจกต์นี้รองรับการติดตั้งและรันระบบ 2 รูปแบบ สามารถดูคู่มืออย่างละเอียดได้ที่:
1. **[Appliance Mode (Local/Docker)](./docs/setup_appliance.md)** - สำหรับการติดตั้งใช้งานภายในองค์กรผ่าน Docker Compose
2. **[SaaS Mode (Cloud)](./docs/setup_saas.md)** - สำหรับการให้บริการบน Public Cloud (Render.com + Vercel)