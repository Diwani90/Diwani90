"""
===================================
منصة ديواني - Seed Data
بيانات تجريبية لمواد البناء
===================================

Run with: python manage.py shell < apps/core/seed_data.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from decimal import Decimal
from django.contrib.gis.geos import Point
from apps.accounts.models import User, VendorProfile, DriverProfile, Address
from apps.stores.models import StoreCategory, Store, StoreWorkingHours
from apps.products.models import ProductCategory, Product

print("🚀 بدء إضافة البيانات التجريبية...")

# ===================================
# 1. فئات المتاجر الرئيسية (مواد البناء)
# ===================================
print("\n📦 إضافة فئات مواد البناء...")

STORE_CATEGORIES = [
    {
        'name': 'الخرسانة والأسمنت',
        'name_en': 'Concrete & Cement',
        'slug': 'concrete-cement',
        'description': 'أسمنت بورتلاندي، خرسانة جاهزة، إضافات الخرسانة، قوالب الخرسانة',
        'commission_rate': 12.00,
        'sort_order': 1,
    },
    {
        'name': 'الحديد والصلب',
        'name_en': 'Iron & Steel',
        'slug': 'iron-steel',
        'description': 'حديد التسليح، الهياكل المعدنية، الأنابيب المعدنية، الألواح المعدنية',
        'commission_rate': 10.00,
        'sort_order': 2,
    },
    {
        'name': 'الطوب والبلوك',
        'name_en': 'Bricks & Blocks',
        'slug': 'bricks-blocks',
        'description': 'الطوب الأحمر، البلوك الخرساني، الطوب المعزول، الطوب الزجاجي',
        'commission_rate': 15.00,
        'sort_order': 3,
    },
    {
        'name': 'مواد العزل',
        'name_en': 'Insulation Materials',
        'slug': 'insulation',
        'description': 'عزل حراري، عزل مائي، عزل صوتي، مواد العزل الحديثة',
        'commission_rate': 18.00,
        'sort_order': 4,
    },
    {
        'name': 'الأبواب والنوافذ',
        'name_en': 'Doors & Windows',
        'slug': 'doors-windows',
        'description': 'أبواب خشبية، أبواب معدنية، نوافذ ألمنيوم، نوافذ PVC',
        'commission_rate': 15.00,
        'sort_order': 5,
    },
    {
        'name': 'السيراميك والبلاط',
        'name_en': 'Ceramics & Tiles',
        'slug': 'ceramics-tiles',
        'description': 'بلاط الأرضيات، بلاط الجدران، السيراميك، الرخام والجرانيت',
        'commission_rate': 15.00,
        'sort_order': 6,
    },
    {
        'name': 'الدهانات والطلاء',
        'name_en': 'Paints & Coatings',
        'slug': 'paints-coatings',
        'description': 'دهانات داخلية، دهانات خارجية، مواد التشطيب، أدوات الطلاء',
        'commission_rate': 20.00,
        'sort_order': 7,
    },
    {
        'name': 'السباكة والكهرباء',
        'name_en': 'Plumbing & Electrical',
        'slug': 'plumbing-electrical',
        'description': 'أنابيب المياه، التجهيزات الصحية، الكابلات الكهربائية، المفاتيح والمقابس',
        'commission_rate': 18.00,
        'sort_order': 8,
    },
]

for cat_data in STORE_CATEGORIES:
    category, created = StoreCategory.objects.get_or_create(
        slug=cat_data['slug'],
        defaults=cat_data
    )
    status = "✅ تم إنشاء" if created else "⏭️ موجود"
    print(f"  {status}: {category.name}")

# ===================================
# 2. إنشاء مستخدمين تجريبيين
# ===================================
print("\n👥 إضافة المستخدمين التجريبيين...")

# Admin User
admin_user, created = User.objects.get_or_create(
    phone_number='+966500000000',
    defaults={
        'first_name': 'مدير',
        'last_name': 'النظام',
        'email': 'admin@diwani.sa',
        'user_type': User.UserType.ADMIN,
        'is_staff': True,
        'is_superuser': True,
        'is_verified': True,
    }
)
if created:
    admin_user.set_password('Admin@123')
    admin_user.save()
    print(f"  ✅ تم إنشاء المدير: {admin_user.phone_number}")

# Vendor Users (Suppliers)
VENDORS = [
    {
        'phone': '+966501111111',
        'first_name': 'محمد',
        'last_name': 'الحربي',
        'email': 'vendor1@diwani.sa',
        'business_name': 'شركة الحربي للأسمنت',
        'business_name_en': 'Al-Harbi Cement Company',
        'commercial_registration': '1010234567',
        'city': 'الرياض',
        'category_slug': 'concrete-cement',
    },
    {
        'phone': '+966502222222',
        'first_name': 'أحمد',
        'last_name': 'العتيبي',
        'email': 'vendor2@diwani.sa',
        'business_name': 'مصنع العتيبي للحديد',
        'business_name_en': 'Al-Otaibi Iron Factory',
        'commercial_registration': '4030345678',
        'city': 'جدة',
        'category_slug': 'iron-steel',
    },
    {
        'phone': '+966503333333',
        'first_name': 'خالد',
        'last_name': 'الدوسري',
        'email': 'vendor3@diwani.sa',
        'business_name': 'مؤسسة الدوسري للطوب',
        'business_name_en': 'Al-Dosari Bricks Est.',
        'commercial_registration': '2050456789',
        'city': 'الدمام',
        'category_slug': 'bricks-blocks',
    },
    {
        'phone': '+966504444444',
        'first_name': 'سعد',
        'last_name': 'القحطاني',
        'email': 'vendor4@diwani.sa',
        'business_name': 'شركة القحطاني للعزل',
        'business_name_en': 'Al-Qahtani Insulation Co.',
        'commercial_registration': '1010567890',
        'city': 'الرياض',
        'category_slug': 'insulation',
    },
    {
        'phone': '+966505555555',
        'first_name': 'فهد',
        'last_name': 'المطيري',
        'email': 'vendor5@diwani.sa',
        'business_name': 'معرض المطيري للسيراميك',
        'business_name_en': 'Al-Mutairi Ceramics',
        'commercial_registration': '4030678901',
        'city': 'جدة',
        'category_slug': 'ceramics-tiles',
    },
    {
        'phone': '+966506666666',
        'first_name': 'عبدالله',
        'last_name': 'الشمري',
        'email': 'vendor6@diwani.sa',
        'business_name': 'دهانات الشمري',
        'business_name_en': 'Al-Shammari Paints',
        'commercial_registration': '2050789012',
        'city': 'الدمام',
        'category_slug': 'paints-coatings',
    },
]

# City coordinates
CITY_COORDS = {
    'الرياض': (24.7136, 46.6753),
    'جدة': (21.4858, 39.1925),
    'الدمام': (26.4207, 50.0888),
    'مكة المكرمة': (21.3891, 39.8579),
    'المدينة المنورة': (24.5247, 39.5692),
}

for vendor_data in VENDORS:
    user, created = User.objects.get_or_create(
        phone_number=vendor_data['phone'],
        defaults={
            'first_name': vendor_data['first_name'],
            'last_name': vendor_data['last_name'],
            'email': vendor_data['email'],
            'user_type': User.UserType.VENDOR,
            'is_verified': True,
        }
    )

    if created:
        user.set_password('Vendor@123')
        user.save()
        print(f"  ✅ تم إنشاء التاجر: {user.full_name}")

    # Create Vendor Profile
    VendorProfile.objects.get_or_create(
        user=user,
        defaults={
            'business_name': vendor_data['business_name'],
            'business_name_en': vendor_data['business_name_en'],
            'commercial_registration': vendor_data['commercial_registration'],
            'status': VendorProfile.VendorStatus.APPROVED,
        }
    )

    # Create Store
    category = StoreCategory.objects.get(slug=vendor_data['category_slug'])
    lat, lng = CITY_COORDS.get(vendor_data['city'], (24.7136, 46.6753))

    store, store_created = Store.objects.get_or_create(
        owner=user,
        defaults={
            'name': vendor_data['business_name'],
            'name_en': vendor_data['business_name_en'],
            'category': category,
            'store_type': Store.StoreType.OTHER,
            'phone_number': vendor_data['phone'],
            'email': vendor_data['email'],
            'address': f'المنطقة الصناعية، {vendor_data["city"]}',
            'city': vendor_data['city'],
            'district': 'المنطقة الصناعية',
            'location': Point(lng, lat, srid=4326),
            'delivery_radius_km': 50,
            'min_order_amount': Decimal('500.00'),
            'delivery_fee': Decimal('100.00'),
            'status': Store.StoreStatus.ACTIVE,
            'is_verified': True,
            'rating': Decimal('4.5'),
        }
    )

    if store_created:
        print(f"  ✅ تم إنشاء المتجر: {store.name}")

# ===================================
# 3. إنشاء عملاء تجريبيين
# ===================================
print("\n🛒 إضافة العملاء التجريبيين...")

CUSTOMERS = [
    {
        'phone': '+966551111111',
        'first_name': 'عمر',
        'last_name': 'السعيد',
        'email': 'customer1@test.com',
    },
    {
        'phone': '+966552222222',
        'first_name': 'يوسف',
        'last_name': 'الأحمد',
        'email': 'customer2@test.com',
    },
    {
        'phone': '+966553333333',
        'first_name': 'ناصر',
        'last_name': 'العنزي',
        'email': 'customer3@test.com',
    },
]

for cust_data in CUSTOMERS:
    user, created = User.objects.get_or_create(
        phone_number=cust_data['phone'],
        defaults={
            'first_name': cust_data['first_name'],
            'last_name': cust_data['last_name'],
            'email': cust_data['email'],
            'user_type': User.UserType.CUSTOMER,
            'is_verified': True,
            'wallet_balance': Decimal('1000.00'),
        }
    )
    if created:
        user.set_password('Customer@123')
        user.save()
        print(f"  ✅ تم إنشاء العميل: {user.full_name}")

# ===================================
# 4. إنشاء سائقين تجريبيين
# ===================================
print("\n🚚 إضافة السائقين التجريبيين...")

DRIVERS = [
    {
        'phone': '+966591111111',
        'first_name': 'سالم',
        'last_name': 'الزهراني',
        'vehicle_type': 'truck',
        'plate_number': 'أ ب ج 1234',
    },
    {
        'phone': '+966592222222',
        'first_name': 'بندر',
        'last_name': 'الغامدي',
        'vehicle_type': 'van',
        'plate_number': 'د هـ و 5678',
    },
]

for driver_data in DRIVERS:
    user, created = User.objects.get_or_create(
        phone_number=driver_data['phone'],
        defaults={
            'first_name': driver_data['first_name'],
            'last_name': driver_data['last_name'],
            'user_type': User.UserType.DRIVER,
            'is_verified': True,
        }
    )

    if created:
        user.set_password('Driver@123')
        user.save()
        print(f"  ✅ تم إنشاء السائق: {user.full_name}")

    DriverProfile.objects.get_or_create(
        user=user,
        defaults={
            'vehicle_type': driver_data['vehicle_type'],
            'vehicle_model': 'ايسوزو NPR',
            'vehicle_year': 2023,
            'vehicle_color': 'أبيض',
            'plate_number': driver_data['plate_number'],
            'status': DriverProfile.DriverStatus.APPROVED,
            'is_online': True,
            'is_available': True,
            'current_location': Point(46.6753, 24.7136, srid=4326),
        }
    )

# ===================================
# 5. إنشاء منتجات تجريبية
# ===================================
print("\n📦 إضافة المنتجات التجريبية...")

# Get stores
stores = Store.objects.filter(status=Store.StoreStatus.ACTIVE)

PRODUCTS = [
    # الخرسانة والأسمنت
    {
        'category_slug': 'concrete-cement',
        'products': [
            {'name': 'أسمنت بورتلاندي عادي', 'name_en': 'Ordinary Portland Cement', 'price': 18.00, 'unit': 'كيس 50 كجم'},
            {'name': 'أسمنت مقاوم للكبريتات', 'name_en': 'Sulfate Resistant Cement', 'price': 22.00, 'unit': 'كيس 50 كجم'},
            {'name': 'خرسانة جاهزة C30', 'name_en': 'Ready Mix Concrete C30', 'price': 280.00, 'unit': 'متر مكعب'},
        ]
    },
    # الحديد والصلب
    {
        'category_slug': 'iron-steel',
        'products': [
            {'name': 'حديد تسليح قطر 12 مم', 'name_en': 'Rebar 12mm', 'price': 2800.00, 'unit': 'طن'},
            {'name': 'حديد تسليح قطر 16 مم', 'name_en': 'Rebar 16mm', 'price': 2850.00, 'unit': 'طن'},
            {'name': 'شبك حديد ملحوم', 'name_en': 'Welded Wire Mesh', 'price': 45.00, 'unit': 'لوح'},
        ]
    },
    # الطوب والبلوك
    {
        'category_slug': 'bricks-blocks',
        'products': [
            {'name': 'بلوك خرساني 20 سم', 'name_en': 'Concrete Block 20cm', 'price': 3.50, 'unit': 'حبة'},
            {'name': 'طوب أحمر', 'name_en': 'Red Brick', 'price': 0.80, 'unit': 'حبة'},
            {'name': 'بلوك معزول', 'name_en': 'Insulated Block', 'price': 8.00, 'unit': 'حبة'},
        ]
    },
    # مواد العزل
    {
        'category_slug': 'insulation',
        'products': [
            {'name': 'لفائف عزل مائي', 'name_en': 'Waterproof Membrane Roll', 'price': 180.00, 'unit': 'لفة'},
            {'name': 'ألواح فوم عازل', 'name_en': 'Foam Insulation Board', 'price': 35.00, 'unit': 'لوح'},
            {'name': 'عزل صوف صخري', 'name_en': 'Rock Wool Insulation', 'price': 45.00, 'unit': 'متر مربع'},
        ]
    },
    # السيراميك والبلاط
    {
        'category_slug': 'ceramics-tiles',
        'products': [
            {'name': 'سيراميك أرضيات 60x60', 'name_en': 'Floor Ceramic 60x60', 'price': 55.00, 'unit': 'متر مربع'},
            {'name': 'بورسلان إسباني', 'name_en': 'Spanish Porcelain', 'price': 120.00, 'unit': 'متر مربع'},
            {'name': 'رخام كريم مارفل', 'name_en': 'Crema Marfil Marble', 'price': 350.00, 'unit': 'متر مربع'},
        ]
    },
    # الدهانات والطلاء
    {
        'category_slug': 'paints-coatings',
        'products': [
            {'name': 'دهان جوتن داخلي', 'name_en': 'Jotun Interior Paint', 'price': 280.00, 'unit': 'جالون 18 لتر'},
            {'name': 'دهان خارجي مقاوم للعوامل', 'name_en': 'Weather Shield Paint', 'price': 350.00, 'unit': 'جالون 18 لتر'},
            {'name': 'معجون تأسيس', 'name_en': 'Primer Putty', 'price': 85.00, 'unit': 'جالون'},
        ]
    },
]

for cat_products in PRODUCTS:
    category = StoreCategory.objects.filter(slug=cat_products['category_slug']).first()
    if not category:
        continue

    # Find a store in this category
    store = stores.filter(category=category).first()
    if not store:
        continue

    # Create product category for the store
    product_cat, _ = ProductCategory.objects.get_or_create(
        store=store,
        slug=cat_products['category_slug'],
        defaults={
            'name': category.name,
            'name_en': category.name_en,
        }
    )

    for prod_data in cat_products['products']:
        product, created = Product.objects.get_or_create(
            store=store,
            slug=prod_data['name_en'].lower().replace(' ', '-'),
            defaults={
                'name': prod_data['name'],
                'name_en': prod_data['name_en'],
                'category': product_cat,
                'price': Decimal(str(prod_data['price'])),
                'description': f"منتج {prod_data['name']} عالي الجودة من {store.name}",
                'stock_quantity': 1000,
                'min_order_quantity': 10,
                'status': Product.ProductStatus.ACTIVE,
                'is_active': True,
            }
        )
        if created:
            print(f"  ✅ تم إنشاء المنتج: {product.name}")

# ===================================
# Done!
# ===================================
print("\n" + "="*50)
print("✅ تم إضافة جميع البيانات التجريبية بنجاح!")
print("="*50)
print(f"""
📊 ملخص البيانات:
  - فئات المتاجر: {StoreCategory.objects.count()}
  - المستخدمين: {User.objects.count()}
  - المتاجر: {Store.objects.count()}
  - المنتجات: {Product.objects.count()}

🔑 بيانات الدخول التجريبية:
  - المدير: +966500000000 / Admin@123
  - التاجر: +966501111111 / Vendor@123
  - العميل: +966551111111 / Customer@123
  - السائق: +966591111111 / Driver@123
""")
