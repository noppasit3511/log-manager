# System Architecture & Data Flow

เอกสารฉบับนี้อธิบายถึงสถาปัตยกรรมของระบบ Mini SIEM, แผนภาพการไหลของข้อมูล (Data Flow) และโมเดลการจัดการข้อมูลผู้ใช้งาน (Tenant Model / RBAC)

## 1. Architecture Diagram
แผนภาพด้านล่างแสดงโครงสร้างของระบบแบบ End-to-End ตั้งแต่การรับข้อมูลจนถึงการแสดงผล

```mermaid
graph LR
    subgraph Log Sources
        API[Modern Apps\nAWS, CrowdStrike, M365] -->|HTTP POST JSON| Ingest(FastAPI Ingest)
        SYS[Legacy Devices\nFirewalls, Routers] -->|UDP 514| UDP(Syslog Server)
    end

    subgraph Backend [Log Manager Backend]
        Ingest --> Norm{Normalization\nPipeline}
        UDP --> Norm
        
        Norm -->|1. Extract Fields\n2. Keep Raw JSON| DB[(PostgreSQL\nJSONB)]
        Norm -->|If Level == ERROR| Alert[Alert Engine]
        
        Auth[AuthN & RBAC] --> Query[Query Engine]
        Query -->|Fetch Filtered Data| DB
    end

    subgraph External & UI
        Alert -->|Webhook| Discord[Discord Channel]
        Dash[Security Dashboard] -->|GET /logs\n+ X-API-Key| Auth
    end