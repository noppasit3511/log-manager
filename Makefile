.PHONY: up down simulate test

up:
	docker-compose up -d --build
	@echo "✅ System is up! Backend: http://localhost:8000, Frontend: open frontend/index.html"

down:
	docker-compose down -v
	@echo "🛑 System is down and data is cleared."

simulate:
	python samples/simulate_4_sources.py