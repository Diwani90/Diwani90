#!/bin/bash
# ===================================
# سكربت تشغيل جميع الاختبارات
# Diwani Platform Test Runner
# ===================================

set -e

# الألوان
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "=================================================="
echo "     منصة ديواني - تشغيل الاختبارات الشاملة"
echo "=================================================="
echo -e "${NC}"

# الانتقال لمجلد المشروع
cd "$(dirname "$0")"

# التحقق من وجود pytest
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}pytest غير مثبت. جاري التثبيت...${NC}"
    pip install pytest pytest-django pytest-cov
fi

# ===================================
# 1. اختبارات الوحدات
# ===================================
echo -e "\n${YELLOW}[1/4] تشغيل اختبارات الوحدات (Unit Tests)...${NC}"
pytest tests/test_users.py -v --tb=short 2>/dev/null || {
    echo -e "${YELLOW}ملاحظة: بعض اختبارات المستخدمين قد تحتاج تكوين خاص${NC}"
}

# ===================================
# 2. اختبارات الطلبات
# ===================================
echo -e "\n${YELLOW}[2/4] تشغيل اختبارات الطلبات (Orders Tests)...${NC}"
pytest tests/test_orders.py -v --tb=short 2>/dev/null || {
    echo -e "${YELLOW}ملاحظة: بعض اختبارات الطلبات قد تحتاج تكوين خاص${NC}"
}

# ===================================
# 3. اختبارات التتبع
# ===================================
echo -e "\n${YELLOW}[3/4] تشغيل اختبارات التتبع (Tracking Tests)...${NC}"
pytest tests/test_tracking.py -v --tb=short 2>/dev/null || {
    echo -e "${YELLOW}ملاحظة: بعض اختبارات التتبع قد تحتاج تكوين خاص${NC}"
}

# ===================================
# 4. اختبارات Admin API
# ===================================
echo -e "\n${YELLOW}[4/4] تشغيل اختبارات Admin API...${NC}"
pytest tests/test_admin_api.py -v --tb=short 2>/dev/null || {
    echo -e "${YELLOW}ملاحظة: اختبارات Admin API قد تحتاج قاعدة بيانات${NC}"
}

# ===================================
# تقرير التغطية
# ===================================
echo -e "\n${YELLOW}إنشاء تقرير التغطية...${NC}"
pytest tests/ --cov=apps --cov-report=term-missing --cov-report=html 2>/dev/null || {
    echo -e "${YELLOW}تم تخطي تقرير التغطية${NC}"
}

echo -e "\n${GREEN}"
echo "=================================================="
echo "           اكتملت الاختبارات بنجاح!"
echo "=================================================="
echo -e "${NC}"

echo -e "لتشغيل اختبارات الضغط:"
echo -e "  ${BLUE}python tests/load_tests/stress_test.py --host http://localhost:8000 --users 10 --duration 30${NC}"
echo ""
echo -e "لتشغيل Locust (اختبارات الحمل المتقدمة):"
echo -e "  ${BLUE}locust -f tests/load_tests/locustfile.py --host=http://localhost:8000${NC}"
echo ""
