# Diwani Backend - خادم ديواني

> Django REST API for Diwani Platform
> واجهة برمجة التطبيقات لمنصة ديواني

---

## التطبيقات / Apps (11)

| App | الوصف | Description |
|-----|-------|-------------|
| `users` | إدارة المستخدمين، OTP، المصادقة | User management, OTP, authentication |
| `products` | كتالوج المنتجات، التصنيفات، البحث | Product catalog, categories, search |
| `orders` | إنشاء الطلبات، التتبع، التوصيل | Order creation, tracking, delivery |
| `finance` | المحفظة، المعاملات، الفواتير | Wallet, transactions, invoices |
| `chat` | الدردشة المشفرة (E2E) | End-to-end encrypted chat |
| `realtime` | WebSocket، الأحداث المباشرة | WebSocket, real-time events |
| `notifications` | FCM، APNS، SMS | Push notifications, SMS |
| `support` | التذاكر، الدعم الفني | Support tickets, help desk |
| `analytics` | الإحصائيات، التقارير | Statistics, reports |
| `core` | النماذج المشتركة | Shared models |
| `search` | Elasticsearch | Full-text search |

---

## البدء السريع / Quick Start

```bash
# 1. إنشاء بيئة افتراضية
python -m venv venv
source venv/bin/activate  # Linux/Mac
# أو على Windows: venv\Scripts\activate

# 2. تثبيت المتطلبات
pip install -r requirements.txt

# 3. نسخ ملف الإعدادات
cp .env.example .env

# 4. تعديل الإعدادات في .env
# Edit DATABASE_URL, SECRET_KEY, etc.

# 5. تشغيل قاعدة البيانات (Docker)
docker-compose up -d postgres redis

# 6. إنشاء الجداول
python manage.py migrate

# 7. إنشاء حساب مدير
python manage.py createsuperuser

# 8. تشغيل السيرفر
python manage.py runserver
```

---

## المتطلبات الأساسية / Requirements

- Python 3.10+
- PostgreSQL 14+ with PostGIS
- Redis 6+
- (Optional) Elasticsearch 8+

---

## الإعدادات / Configuration

راجع ملف `.env.example` للحصول على قائمة كاملة بالإعدادات المطلوبة.

See `.env.example` for complete list of required settings.

### إعدادات مهمة / Important Settings

1. **SMS** - Unifonic (للسعودية) أو Twilio
2. **Payment** - Tap Payment
3. **Notifications** - FCM (Android/Web) + APNS (iOS)
4. **Encryption** - FIELD_ENCRYPTION_KEY + CHAT_ENCRYPTION_KEY

---

## API Documentation

- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

---

## اختبار الـ Test Mode

جميع الخدمات الخارجية تدعم وضع الاختبار:

```env
SMS_CONFIG__TEST_MODE=True              # SMS يُطبع في console
TAP_PAYMENT_CONFIG__TEST_MODE=True      # دفع وهمي محلي
FCM_CONFIG__TEST_MODE=True              # إشعارات تُطبع في console
APNS_CONFIG__TEST_MODE=True             # إشعارات تُطبع في console
```
