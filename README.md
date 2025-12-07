# Diwani Platform - منصة ديواني

> منصة سعودية لتجارة مواد البناء
> Saudi Arabian Construction Materials E-commerce Platform

---

## هيكل المشروع / Project Structure

```
Diwani90/
├── diwani-platform/          # <-- المشروع الرئيسي / MAIN PROJECT
│   ├── backend/              # Django Backend API (11 تطبيق/apps)
│   │   ├── apps/
│   │   │   ├── users/        # المستخدمين والمصادقة
│   │   │   ├── products/     # المنتجات والكتالوج
│   │   │   ├── orders/       # الطلبات والتوصيل
│   │   │   ├── finance/      # المالية والمحفظة
│   │   │   ├── chat/         # الدردشة المشفرة
│   │   │   ├── realtime/     # WebSocket للاتصال المباشر
│   │   │   ├── notifications/# الإشعارات (FCM/APNS/SMS)
│   │   │   ├── support/      # الدعم الفني
│   │   │   ├── analytics/    # التحليلات
│   │   │   ├── core/         # النواة المشتركة
│   │   │   └── search/       # البحث
│   │   └── .env.example      # <-- نموذج الإعدادات (انسخه إلى .env)
│   └── docker-compose.yml
│
├── frontend/                  # React Frontend
│   └── .env                   # إعدادات الواجهة
│
└── backend/                   # (قديم - لا تستخدمه)
    └── server.py              # نموذج أولي بسيط
```

---

## كيفية تشغيل المشروع / How to Run

### 1. إعداد Backend الرئيسي

```bash
# انتقل إلى مجلد Backend الرئيسي
cd diwani-platform/backend

# انسخ ملف الإعدادات
cp .env.example .env

# عدّل الإعدادات في ملف .env
# Edit settings in .env file

# تثبيت المتطلبات
pip install -r requirements.txt

# إنشاء قاعدة البيانات
python manage.py migrate

# تشغيل السيرفر
python manage.py runserver
```

### 2. إعداد Frontend

```bash
cd frontend

# تثبيت المتطلبات
yarn install

# تشغيل في وضع التطوير
yarn start
```

---

## ملفات .env المهمة

| الملف | الموقع | الغرض |
|-------|--------|-------|
| `.env.example` | `diwani-platform/backend/` | نموذج إعدادات Django - **انسخه إلى .env** |
| `.env` | `frontend/` | إعدادات React (عنوان الخادم) |

**ملاحظة مهمة:** ملف `backend/.env` في المجلد الرئيسي هو لنموذج قديم ولا حاجة له.

---

## الميزات المضافة / Features Added

- SMS via Unifonic (Saudi Arabia) + Twilio
- Tap Payment integration
- FCM (Android/Web) + APNS (iOS) notifications
- End-to-end encrypted chat (AES-256-GCM)
- WebSocket real-time communication
- PDF invoice generation (Arabic support)
- Referral system with wallet rewards
- Driver delivery tracking with ETA

---

## للمساعدة / For Help

راجع ملف `.env.example` للحصول على شرح تفصيلي لكل إعداد.

See `.env.example` file for detailed explanation of each setting.
