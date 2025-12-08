# دليل الاختبارات الشامل - منصة ديواني
# Diwani Platform Testing Guide

## 📋 نظرة عامة

يتضمن هذا المشروع ثلاثة أنواع من الاختبارات:
1. **اختبارات الوحدات (Unit Tests)** - اختبار الدوال والنماذج
2. **اختبارات التكامل (Integration Tests)** - اختبار APIs و workflows
3. **اختبارات الضغط (Load Tests)** - اختبار الأداء تحت الحمل

---

## 🚀 التشغيل السريع

### تثبيت متطلبات الاختبار
```bash
pip install -r requirements-test.txt
```

### تشغيل جميع الاختبارات
```bash
# من داخل Docker
docker compose exec backend pytest tests/ -v

# أو محلياً
cd diwani-platform/backend
./run_tests.sh
```

---

## 📁 هيكل الاختبارات

```
tests/
├── __init__.py
├── conftest.py              # إعدادات pytest والـ fixtures
├── test_users.py            # اختبارات المستخدمين
├── test_orders.py           # اختبارات الطلبات
├── test_tracking.py         # اختبارات التتبع
├── test_admin_api.py        # اختبارات Admin APIs
└── load_tests/
    ├── __init__.py
    ├── locustfile.py        # اختبارات Locust
    └── stress_test.py       # اختبار ضغط بسيط
```

---

## 🧪 اختبارات الوحدات والتكامل

### تشغيل الاختبارات

```bash
# جميع الاختبارات
pytest tests/ -v

# اختبارات محددة
pytest tests/test_users.py -v
pytest tests/test_admin_api.py -v

# مع تغطية الكود
pytest tests/ --cov=apps --cov-report=html

# تشغيل متوازي (أسرع)
pytest tests/ -n auto
```

### ملفات الاختبار

#### `test_users.py`
- إنشاء المستخدمين (عميل، بائع، سائق، مدير)
- خدمة OTP (توليد، تحقق، انتهاء صلاحية)
- خدمة المصادقة (JWT tokens)
- التسجيل

#### `test_admin_api.py`
- إدارة المستخدمين (قائمة، تفاصيل، تحديث، حذف)
- إدارة البائعين (توثيق، رفض)
- إدارة السائقين
- الإحصائيات

---

## 📊 اختبارات الضغط (Load Testing)

### 1. اختبار الضغط البسيط

```bash
# تشغيل اختبار بسيط (10 مستخدمين، 30 ثانية)
python tests/load_tests/stress_test.py \
    --host http://localhost:8000 \
    --users 10 \
    --duration 30

# اختبار متوسط (50 مستخدم، دقيقة)
python tests/load_tests/stress_test.py \
    --host http://localhost:8000 \
    --users 50 \
    --duration 60

# اختبار مكثف (100 مستخدم، 5 دقائق)
python tests/load_tests/stress_test.py \
    --host http://localhost:8000 \
    --users 100 \
    --duration 300
```

### 2. اختبار Locust (متقدم)

```bash
# تثبيت Locust
pip install locust

# تشغيل مع واجهة ويب
locust -f tests/load_tests/locustfile.py --host=http://localhost:8000
# افتح http://localhost:8089

# تشغيل بدون واجهة
locust -f tests/load_tests/locustfile.py \
    --host=http://localhost:8000 \
    --headless \
    -u 100 \    # عدد المستخدمين
    -r 10 \     # معدل الإضافة
    -t 60s      # المدة
```

### سيناريوهات الاختبار في Locust

| السيناريو | الوزن | الوصف |
|-----------|-------|-------|
| CustomerUser | 5 | محاكاة سلوك العميل |
| VendorUser | 2 | محاكاة سلوك البائع |
| DriverUser | 1 | محاكاة سلوك السائق |
| AdminUser | 1 | محاكاة سلوك المدير |

---

## 📈 قراءة النتائج

### نتائج اختبار الضغط

```
تقرير اختبار الضغط
==================================================

معلومات الاختبار:
  - المدة الفعلية: 30.05 ثانية
  - عدد المستخدمين: 10

إحصائيات الطلبات:
  - إجمالي الطلبات: 156
  - الطلبات الناجحة: 154
  - الطلبات الفاشلة: 2
  - نسبة النجاح: 98.72%
  - الطلبات/ثانية: 5.19

أوقات الاستجابة (ميلي ثانية):
  - المتوسط: 45.32 ms
  - P50 (الوسيط): 38.00 ms
  - P95: 125.00 ms
  - P99: 245.00 ms
```

### معايير الأداء الجيد

| المؤشر | جيد | مقبول | يحتاج تحسين |
|--------|-----|-------|-------------|
| نسبة النجاح | >99% | 95-99% | <95% |
| متوسط الاستجابة | <200ms | 200-500ms | >500ms |
| P95 | <500ms | 500-1000ms | >1000ms |
| P99 | <1000ms | 1-2s | >2s |

---

## 🔧 إعداد بيئة الاختبار

### متطلبات قاعدة البيانات
```python
# في conftest.py
@pytest.fixture(scope='session')
def django_db_setup():
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
```

### Fixtures المتاحة

```python
# المستخدمين
customer_user      # عميل
vendor_user        # بائع
driver_user        # سائق
admin_user         # مدير

# المتاجر والمنتجات
store              # متجر
category           # تصنيف
product            # منتج

# الطلبات
order              # طلب
delivery           # توصيل

# المصادقة
customer_auth_headers
vendor_auth_headers
driver_auth_headers
admin_auth_headers
```

---

## 🐛 حل المشاكل

### خطأ: Database not configured
```bash
export DJANGO_SETTINGS_MODULE=config.settings.test
```

### خطأ: Module not found
```bash
pip install -r requirements-test.txt
```

### خطأ: Connection refused (اختبار الضغط)
تأكد من أن الخادم يعمل:
```bash
docker compose up -d
curl http://localhost:8000/health/
```

---

## 📝 إضافة اختبارات جديدة

### مثال: اختبار endpoint جديد

```python
@pytest.mark.django_db
class TestNewFeature:
    """اختبارات الميزة الجديدة"""

    def test_feature_success(self, api_client, customer_auth_headers):
        """اختبار النجاح"""
        response = api_client.get(
            '/api/v1/new-feature/',
            **customer_auth_headers
        )
        assert response.status_code == 200

    def test_feature_unauthorized(self, api_client):
        """اختبار بدون مصادقة"""
        response = api_client.get('/api/v1/new-feature/')
        assert response.status_code == 401
```

---

## 📞 الدعم

للمساعدة في الاختبارات:
- راجع `conftest.py` للـ fixtures
- راجع الاختبارات الموجودة كأمثلة
- استخدم `-v` للحصول على تفاصيل أكثر
