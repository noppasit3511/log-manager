.PHONY: up down simulate test clean

up:
	docker-compose up -d --build
	@echo "✅ ระบบพร้อมใช้งาน! Backend: http://localhost:8000, Frontend: open frontend/index.html"

down:
	docker-compose down -v
	@echo "🛑 ปิดระบบและล้างข้อมูลใน Database เรียบร้อย"

simulate:
	python samples/simulate_4_sources.py

test:
	pytest tests/test_api.py -v
	@echo "🧪 ทดสอบระบบ API สำเร็จ!"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "🧹 ล้างไฟล์ขยะ Python เรียบร้อย"