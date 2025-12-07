#!/usr/bin/env python
"""
سكريبت إعداد قاعدة البيانات لمنصة ديواني
==========================================

يقوم بإنشاء الـ migrations وتطبيقها وإضافة البيانات الأولية

الاستخدام:
    python setup_database.py
"""

import os
import sys
import django

# إضافة مسار المشروع
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# إعداد Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

try:
    django.setup()
except Exception as e:
    print(f"خطأ في إعداد Django: {e}")
    print("\nتأكد من:")
    print("1. تفعيل البيئة الافتراضية: source venv/bin/activate")
    print("2. تثبيت المتطلبات: pip install -r requirements.txt")
    print("3. وجود ملف .env")
    sys.exit(1)

from django.core.management import execute_from_command_line


def run_command(command_args):
    """تنفيذ أمر Django"""
    print(f"\n{'='*50}")
    print(f"تنفيذ: python manage.py {' '.join(command_args)}")
    print('='*50)
    try:
        execute_from_command_line(['manage.py'] + command_args)
        return True
    except Exception as e:
        print(f"خطأ: {e}")
        return False


def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║         إعداد قاعدة بيانات منصة ديواني                    ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    # قائمة التطبيقات
    apps = [
        'users',
        'products',
        'stores',
        'orders',
        'chat',
        'finance',
        'notifications',
        'tracking',
        'search',
        'realtime',
    ]

    # 1. إنشاء migrations
    print("\n📦 الخطوة 1: إنشاء ملفات الـ migrations...")
    for app in apps:
        print(f"\n  ➤ إنشاء migrations لـ {app}...")
        run_command(['makemigrations', app])

    # 2. عرض الـ migrations المُنشأة
    print("\n📋 الخطوة 2: عرض الـ migrations...")
    run_command(['showmigrations'])

    # 3. تطبيق الـ migrations
    print("\n🔧 الخطوة 3: تطبيق الـ migrations...")
    run_command(['migrate'])

    # 4. إنشاء مستخدم مسؤول (اختياري)
    print("\n👤 الخطوة 4: إنشاء مستخدم مسؤول...")
    create_admin = input("هل تريد إنشاء مستخدم مسؤول؟ (y/n): ").strip().lower()

    if create_admin == 'y':
        from apps.users.models import User

        phone = input("رقم الهاتف (مثال: 0512345678): ").strip()

        if not phone:
            phone = '0500000000'

        # تطبيع رقم الهاتف
        if phone.startswith('05'):
            phone = '+966' + phone[1:]
        elif phone.startswith('5'):
            phone = '+966' + phone

        try:
            admin_user, created = User.objects.get_or_create(
                phone_number=phone,
                defaults={
                    'user_type': 'admin',
                    'is_staff': True,
                    'is_superuser': True,
                    'is_verified': True,
                    'phone_verified': True,
                    'first_name': 'مسؤول',
                    'last_name': 'النظام',
                }
            )

            if created:
                admin_user.set_password('admin123')
                admin_user.save()
                print(f"✅ تم إنشاء المسؤول: {phone}")
                print(f"   كلمة المرور الافتراضية: admin123")
            else:
                print(f"ℹ️ المستخدم موجود مسبقاً: {phone}")
        except Exception as e:
            print(f"❌ خطأ في إنشاء المسؤول: {e}")

    # 5. إضافة بيانات أولية
    print("\n📊 الخطوة 5: إضافة البيانات الأولية...")
    add_seed = input("هل تريد إضافة بيانات تجريبية؟ (y/n): ").strip().lower()

    if add_seed == 'y':
        seed_initial_data()

    # 6. التحقق النهائي
    print("\n✅ الخطوة 6: التحقق النهائي...")
    run_command(['check'])

    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║              ✅ اكتمل الإعداد بنجاح!                       ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  الخطوات التالية:                                         ║
    ║  1. تشغيل الخادم: python manage.py runserver              ║
    ║  2. فتح API Docs: http://localhost:8000/api/v1/docs       ║
    ║  3. لوحة الإدارة: http://localhost:8000/admin             ║
    ╚═══════════════════════════════════════════════════════════╝
    """)


def seed_initial_data():
    """إضافة البيانات الأولية"""
    from apps.products.models import Category

    # الأقسام الرئيسية
    categories_data = [
        {
            'name': 'مواد البناء',
            'name_en': 'Building Materials',
            'slug': 'building-materials',
            'icon': 'building',
            'color': '#2196F3',
            'category_type': 'products',
        },
        {
            'name': 'معدات البناء',
            'name_en': 'Construction Equipment',
            'slug': 'construction-equipment',
            'icon': 'truck',
            'color': '#FF9800',
            'category_type': 'rentals',
        },
        {
            'name': 'خدمات لوجستية',
            'name_en': 'Logistics Services',
            'slug': 'logistics',
            'icon': 'delivery',
            'color': '#4CAF50',
            'category_type': 'logistics',
        },
        {
            'name': 'خدمات المقاولات',
            'name_en': 'Contracting Services',
            'slug': 'contracting',
            'icon': 'tools',
            'color': '#9C27B0',
            'category_type': 'services',
        },
    ]

    print("  ➤ إضافة الأقسام الرئيسية...")
    for cat_data in categories_data:
        cat, created = Category.objects.get_or_create(
            slug=cat_data['slug'],
            defaults=cat_data
        )
        if created:
            print(f"    ✓ {cat.name}")

    # أقسام فرعية لمواد البناء
    building_materials = Category.objects.filter(slug='building-materials').first()
    if building_materials:
        sub_categories = [
            {'name': 'أسمنت', 'name_en': 'Cement', 'slug': 'cement'},
            {'name': 'حديد تسليح', 'name_en': 'Reinforcing Steel', 'slug': 'steel'},
            {'name': 'طوب وبلوك', 'name_en': 'Bricks & Blocks', 'slug': 'bricks'},
            {'name': 'خرسانة جاهزة', 'name_en': 'Ready Mix Concrete', 'slug': 'concrete'},
            {'name': 'رمل وحصى', 'name_en': 'Sand & Gravel', 'slug': 'sand-gravel'},
            {'name': 'دهانات', 'name_en': 'Paints', 'slug': 'paints'},
            {'name': 'عزل', 'name_en': 'Insulation', 'slug': 'insulation'},
            {'name': 'أدوات صحية', 'name_en': 'Sanitary Ware', 'slug': 'sanitary'},
            {'name': 'كهربائيات', 'name_en': 'Electrical', 'slug': 'electrical'},
            {'name': 'سباكة', 'name_en': 'Plumbing', 'slug': 'plumbing'},
        ]

        print("  ➤ إضافة الأقسام الفرعية...")
        for sub in sub_categories:
            sub['parent'] = building_materials
            sub['category_type'] = 'products'
            cat, created = Category.objects.get_or_create(
                slug=sub['slug'],
                defaults=sub
            )
            if created:
                print(f"    ✓ {cat.name}")

    # قواعد العمولة
    from apps.finance.models import CommissionRule

    print("  ➤ إضافة قواعد العمولة...")
    CommissionRule.objects.get_or_create(
        name='العمولة الافتراضية',
        defaults={
            'applies_to': 'all',
            'platform_percentage': 10,
            'min_commission': 1,
            'is_active': True,
        }
    )
    print("    ✓ العمولة الافتراضية (10%)")

    print("\n  ✅ تمت إضافة البيانات الأولية")


if __name__ == '__main__':
    main()
