# =============================================================================
# منصة ديواني - أوامر Docker والتطوير
# Diwani Platform - Docker & Development Commands
# =============================================================================

.PHONY: help build up down restart logs shell migrate test lint clean

# المساعدة
help:
	@echo "==================================="
	@echo "منصة ديواني - الأوامر المتاحة"
	@echo "==================================="
	@echo ""
	@echo "Docker Commands:"
	@echo "  make build      - بناء الصور Docker images"
	@echo "  make up         - تشغيل جميع الخدمات"
	@echo "  make down       - إيقاف جميع الخدمات"
	@echo "  make restart    - إعادة تشغيل الخدمات"
	@echo "  make logs       - عرض السجلات"
	@echo ""
	@echo "Development Commands:"
	@echo "  make shell      - دخول shell للـ backend"
	@echo "  make migrate    - تشغيل database migrations"
	@echo "  make test       - تشغيل الاختبارات"
	@echo "  make lint       - فحص الكود"
	@echo "  make clean      - تنظيف الملفات المؤقتة"
	@echo ""
	@echo "Database Commands:"
	@echo "  make dbshell    - دخول PostgreSQL shell"
	@echo "  make dumpdb     - تصدير قاعدة البيانات"
	@echo ""

# =============================================================================
# Docker Commands
# =============================================================================

# بناء الصور
build:
	docker-compose build

# تشغيل الخدمات
up:
	docker-compose up -d
	@echo "✅ Services started!"
	@echo "📍 Backend: http://localhost:8000"
	@echo "📍 API Docs: http://localhost:8000/api/docs"
	@echo "📍 Flower: http://localhost:5555"
	@echo "📍 Kibana: http://localhost:5601"

# تشغيل مع عرض السجلات
up-logs:
	docker-compose up

# إيقاف الخدمات
down:
	docker-compose down

# إيقاف مع حذف الأحجام
down-volumes:
	docker-compose down -v

# إعادة التشغيل
restart:
	docker-compose restart

# إعادة بناء وتشغيل
rebuild:
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d

# عرض السجلات
logs:
	docker-compose logs -f

# سجلات backend فقط
logs-backend:
	docker-compose logs -f backend

# سجلات celery
logs-celery:
	docker-compose logs -f celery_worker celery_beat

# =============================================================================
# Development Commands
# =============================================================================

# دخول shell
shell:
	docker-compose exec backend python manage.py shell

# bash shell
bash:
	docker-compose exec backend bash

# Django migrations
migrate:
	docker-compose exec backend python manage.py migrate

# إنشاء migrations
makemigrations:
	docker-compose exec backend python manage.py makemigrations

# إنشاء superuser
createsuperuser:
	docker-compose exec backend python manage.py createsuperuser

# جمع الملفات الثابتة
collectstatic:
	docker-compose exec backend python manage.py collectstatic --noinput

# تشغيل الاختبارات
test:
	docker-compose exec backend pytest -v

# تشغيل اختبارات محددة
test-app:
	docker-compose exec backend pytest tests/test_$(app).py -v

# فحص الكود
lint:
	docker-compose exec backend flake8 apps/
	docker-compose exec backend black --check apps/

# تنسيق الكود
format:
	docker-compose exec backend black apps/
	docker-compose exec backend isort apps/

# =============================================================================
# Database Commands
# =============================================================================

# دخول PostgreSQL
dbshell:
	docker-compose exec db psql -U diwani_user -d diwani_db

# تصدير قاعدة البيانات
dumpdb:
	docker-compose exec db pg_dump -U diwani_user diwani_db > backup_$(shell date +%Y%m%d_%H%M%S).sql

# استيراد قاعدة البيانات
loaddb:
	docker-compose exec -T db psql -U diwani_user -d diwani_db < $(file)

# =============================================================================
# Elasticsearch Commands
# =============================================================================

# إنشاء الفهارس
es-create-indexes:
	docker-compose exec backend python manage.py search_index --create

# إعادة بناء الفهارس
es-rebuild-indexes:
	docker-compose exec backend python manage.py search_index --rebuild

# =============================================================================
# Cleanup Commands
# =============================================================================

# تنظيف الملفات المؤقتة
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete

# تنظيف Docker
docker-clean:
	docker system prune -f
	docker volume prune -f

# =============================================================================
# Production Commands (use with caution!)
# =============================================================================

# نشر للإنتاج
deploy-prod:
	@echo "⚠️  هل أنت متأكد من النشر للإنتاج؟"
	@read -p "اكتب 'yes' للمتابعة: " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		docker-compose -f docker-compose.prod.yml build; \
		docker-compose -f docker-compose.prod.yml up -d; \
	else \
		echo "تم الإلغاء"; \
	fi
