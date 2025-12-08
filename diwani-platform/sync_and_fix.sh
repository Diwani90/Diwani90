#!/bin/bash
# ==========================================
# سكريبت مزامنة وإصلاح منصة ديواني
# ==========================================

echo "🔄 بدء المزامنة..."

# الألوان
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. إيقاف الحاويات
echo -e "${YELLOW}⏹️  إيقاف الحاويات...${NC}"
docker-compose down

# 2. نسخ جميع ملفات backend إلى الحاوية
echo -e "${YELLOW}📁 مزامنة ملفات backend...${NC}"

# تشغيل الحاويات الأساسية
docker-compose up -d db redis

# انتظار قاعدة البيانات
echo "⏳ انتظار قاعدة البيانات..."
sleep 10

# تشغيل backend
docker-compose up -d backend

# انتظار الحاوية
sleep 5

# نسخ الملفات المحدثة
echo -e "${YELLOW}📋 نسخ الملفات المحدثة...${NC}"

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

echo -e "${GREEN}✅ تم نسخ الملفات${NC}"

# 3. إعادة تشغيل الحاوية
echo -e "${YELLOW}🔄 إعادة تشغيل الحاوية...${NC}"
docker-compose restart backend

# انتظار
sleep 10

# 4. تطبيق migrations
echo -e "${YELLOW}🗄️ تطبيق migrations...${NC}"
docker-compose exec -T backend python manage.py migrate --noinput

# 5. فحص النظام
echo -e "${YELLOW}🔍 فحص النظام...${NC}"
docker-compose exec -T backend python manage.py check

# 6. عرض حالة الحاويات
echo -e "${YELLOW}📊 حالة الحاويات:${NC}"
docker-compose ps

echo ""
echo -e "${GREEN}✅ اكتملت المزامنة!${NC}"
echo ""
echo "للتحقق من السجلات:"
echo "  docker-compose logs -f backend"
echo ""
echo "للوصول إلى API:"
echo "  http://localhost:8000/api/"
echo ""
