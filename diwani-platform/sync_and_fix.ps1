# ==========================================
# سكريبت مزامنة وإصلاح منصة ديواني (Windows)
# ==========================================

Write-Host "🔄 بدء المزامنة..." -ForegroundColor Cyan

# 1. سحب آخر التحديثات من git
Write-Host "📥 سحب آخر التحديثات..." -ForegroundColor Yellow
git pull origin claude/fix-realtime-connection-01PKyEGVHFYSKy36zJSnk3ac

# 2. إيقاف الحاويات
Write-Host "⏹️ إيقاف الحاويات..." -ForegroundColor Yellow
docker-compose down

# 3. تشغيل الحاويات الأساسية
Write-Host "🚀 تشغيل الحاويات..." -ForegroundColor Yellow
docker-compose up -d db redis
Start-Sleep -Seconds 10

docker-compose up -d backend
Start-Sleep -Seconds 5

# 4. نسخ الملفات المحدثة
Write-Host "📋 نسخ الملفات المحدثة..." -ForegroundColor Yellow

# Finance app
docker cp backend/apps/finance/admin.py diwani_backend:/app/apps/finance/admin.py
docker cp backend/apps/finance/models.py diwani_backend:/app/apps/finance/models.py
docker cp backend/apps/finance/api.py diwani_backend:/app/apps/finance/api.py
docker cp backend/apps/finance/schemas.py diwani_backend:/app/apps/finance/schemas.py

# Search app
docker cp backend/apps/search/signals.py diwani_backend:/app/apps/search/signals.py

# Orders app
docker cp backend/apps/orders/models.py diwani_backend:/app/apps/orders/models.py

# Tracking app
docker cp backend/apps/tracking/models.py diwani_backend:/app/apps/tracking/models.py

# Settings
docker cp backend/config/settings/base.py diwani_backend:/app/config/settings/base.py
docker cp backend/config/settings/local.py diwani_backend:/app/config/settings/local.py

Write-Host "✅ تم نسخ الملفات" -ForegroundColor Green

# 5. إعادة تشغيل
Write-Host "🔄 إعادة تشغيل الحاوية..." -ForegroundColor Yellow
docker-compose restart backend
Start-Sleep -Seconds 10

# 6. تطبيق migrations
Write-Host "🗄️ تطبيق migrations..." -ForegroundColor Yellow
docker-compose exec backend python manage.py migrate --noinput

# 7. فحص النظام
Write-Host "🔍 فحص النظام..." -ForegroundColor Yellow
docker-compose exec backend python manage.py check

# 8. عرض الحالة
Write-Host "`n📊 حالة الحاويات:" -ForegroundColor Yellow
docker-compose ps

Write-Host "`n✅ اكتملت المزامنة!" -ForegroundColor Green
Write-Host "`nللتحقق من السجلات:" -ForegroundColor Cyan
Write-Host "  docker-compose logs -f backend"
Write-Host "`nللوصول إلى API:" -ForegroundColor Cyan
Write-Host "  http://localhost:8000/api/"
