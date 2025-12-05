#!/usr/bin/env python3
import os
import sys
import json
sys.path.insert(0, os.path.dirname(__file__))

from src.models.user import db
from src.models.supplier import Supplier
from src.models.category import Category
from src.models.product import Product
from src.models.order import Order, OrderItem
from src.main import app

def seed_categories():
    """إضافة الفئات الأساسية"""
    categories_data = [
        {
            'name': 'خرسانة وأسمنت',
            'name_en': 'concrete_cement',
            'description': 'جميع أنواع الخرسانة والأسمنت ومواد البناء الأساسية',
            'icon': 'Building2',
            'color': 'text-blue-600'
        },
        {
            'name': 'حديد وصلب',
            'name_en': 'iron_steel',
            'description': 'حديد التسليح والصلب بجميع الأنواع والمقاسات',
            'icon': 'Hammer',
            'color': 'text-gray-600'
        },
        {
            'name': 'طوب وبلوك',
            'name_en': 'brick_block',
            'description': 'الطوب الأحمر والبلوك الخرساني وطوب العزل',
            'icon': 'Brick',
            'color': 'text-red-600'
        },
        {
            'name': 'عزل',
            'name_en': 'insulation',
            'description': 'مواد العزل الحراري والمائي والصوتي',
            'icon': 'Shield',
            'color': 'text-green-600'
        },
        {
            'name': 'أبواب ونوافذ',
            'name_en': 'doors_windows',
            'description': 'الأبواب والنوافذ الخشبية والألمنيوم والحديدية',
            'icon': 'Door',
            'color': 'text-brown-600'
        },
        {
            'name': 'سيراميك وبلاط',
            'name_en': 'ceramic_tiles',
            'description': 'السيراميك والبورسلين والرخام والجرانيت',
            'icon': 'Palette',
            'color': 'text-purple-600'
        },
        {
            'name': 'سباكة',
            'name_en': 'plumbing',
            'description': 'أنابيب وتجهيزات السباكة والصرف الصحي',
            'icon': 'Wrench',
            'color': 'text-blue-500'
        },
        {
            'name': 'كهرباء',
            'name_en': 'electrical',
            'description': 'الكابلات والمفاتيح واللوحات الكهربائية',
            'icon': 'Zap',
            'color': 'text-yellow-600'
        }
    ]
    
    for cat_data in categories_data:
        existing = Category.query.filter_by(name=cat_data['name']).first()
        if not existing:
            category = Category(**cat_data)
            db.session.add(category)
    
    db.session.commit()
    print("✅ تم إضافة الفئات بنجاح")

def seed_suppliers():
    """إضافة الموردين التجريبيين"""
    suppliers_data = [
        {
            'name': 'شركة العمران للمواد',
            'description': 'متخصصون في توريد مواد البناء عالية الجودة منذ أكثر من 15 عام. نوفر جميع أنواع الخرسانة والحديد والطوب بأفضل الأسعار.',
            'email': 'info@omran-materials.sa',
            'phone': '+966 11 123 4567',
            'address': 'شارع الملك فهد، حي العليا',
            'city': 'الرياض',
            'rating': 4.8,
            'reviews_count': 156,
            'verified': True,
            'specialties': json.dumps(['خرسانة', 'حديد', 'طوب'])
        },
        {
            'name': 'مؤسسة البناء الحديث',
            'description': 'رائدون في مجال مواد التشطيب والعزل بأحدث التقنيات. نقدم حلول متكاملة لجميع احتياجات البناء والتشطيب.',
            'email': 'sales@modern-build.sa',
            'phone': '+966 12 234 5678',
            'address': 'طريق الملك عبدالعزيز، حي الروضة',
            'city': 'جدة',
            'rating': 4.9,
            'reviews_count': 203,
            'verified': True,
            'specialties': json.dumps(['عزل', 'سيراميك', 'دهانات'])
        },
        {
            'name': 'شركة الخليج للحديد',
            'description': 'متخصصون في توريد الحديد والصلب بجميع الأنواع والمقاسات. نضمن الجودة العالية والتسليم في الوقت المحدد.',
            'email': 'orders@gulf-steel.sa',
            'phone': '+966 13 345 6789',
            'address': 'الطريق الصناعي الثاني، المنطقة الصناعية',
            'city': 'الدمام',
            'rating': 4.7,
            'reviews_count': 89,
            'verified': True,
            'specialties': json.dumps(['حديد', 'صلب', 'معادن'])
        },
        {
            'name': 'مصنع الأبواب الذهبية',
            'description': 'صناعة وتوريد الأبواب والنوافذ بأعلى معايير الجودة. نستخدم أفضل أنواع الخشب والألمنيوم.',
            'email': 'info@golden-doors.sa',
            'phone': '+966 11 456 7890',
            'address': 'المنطقة الصناعية الثانية، طريق الخرج',
            'city': 'الرياض',
            'rating': 4.6,
            'reviews_count': 124,
            'verified': False,
            'specialties': json.dumps(['أبواب', 'نوافذ', 'ألمنيوم'])
        },
        {
            'name': 'شركة النجم للسيراميك',
            'description': 'أكبر مستورد للسيراميك والبورسلين في المنطقة الغربية. نوفر أحدث التصاميم والألوان العصرية.',
            'email': 'sales@star-ceramic.sa',
            'phone': '+966 12 567 8901',
            'address': 'شارع فلسطين، حي الزهراء',
            'city': 'جدة',
            'rating': 4.5,
            'reviews_count': 178,
            'verified': True,
            'specialties': json.dumps(['سيراميك', 'بورسلين', 'رخام'])
        },
        {
            'name': 'مؤسسة الكهرباء المتقدمة',
            'description': 'توريد جميع المواد الكهربائية والإلكترونية للمشاريع السكنية والتجارية والصناعية.',
            'email': 'info@advanced-electric.sa',
            'phone': '+966 13 678 9012',
            'address': 'شارع الأمير محمد بن فهد، حي الفيصلية',
            'city': 'الدمام',
            'rating': 4.4,
            'reviews_count': 95,
            'verified': True,
            'specialties': json.dumps(['كهرباء', 'كابلات', 'إضاءة'])
        }
    ]
    
    for sup_data in suppliers_data:
        existing = Supplier.query.filter_by(email=sup_data['email']).first()
        if not existing:
            supplier = Supplier(**sup_data)
            db.session.add(supplier)
    
    db.session.commit()
    print("✅ تم إضافة الموردين بنجاح")

def seed_products():
    """إضافة المنتجات التجريبية"""
    # Get categories and suppliers
    categories = {cat.name_en: cat.id for cat in Category.query.all()}
    suppliers = {sup.name: sup.id for sup in Supplier.query.all()}
    
    products_data = [
        # خرسانة وأسمنت
        {
            'name': 'أسمنت بورتلاندي عادي 50 كيلو',
            'description': 'أسمنت بورتلاندي عادي عالي الجودة مطابق للمواصفات السعودية، مناسب لجميع أعمال البناء والخرسانة.',
            'price': 25.50,
            'unit': 'كيس',
            'minimum_order': 10,
            'stock_quantity': 1000,
            'sku': 'CEM-PORT-50',
            'brand': 'أسمنت اليمامة',
            'specifications': json.dumps({
                'الوزن': '50 كيلو',
                'النوع': 'بورتلاندي عادي',
                'المقاومة': '42.5 نيوتن/مم²',
                'التعبئة': 'أكياس ورقية'
            }),
            'images': json.dumps(['/images/cement-bag.jpg']),
            'featured': True,
            'category_id': categories['concrete_cement'],
            'supplier_id': suppliers['شركة العمران للمواد']
        },
        {
            'name': 'خرسانة جاهزة C25',
            'description': 'خرسانة جاهزة بمقاومة 25 نيوتن/مم² مناسبة للأساسات والأعمدة والجدران الحاملة.',
            'price': 180.00,
            'unit': 'متر مكعب',
            'minimum_order': 3,
            'stock_quantity': 50,
            'sku': 'CON-C25-M3',
            'brand': 'خرسانة الرياض',
            'specifications': json.dumps({
                'المقاومة': '25 نيوتن/مم²',
                'الهبوط': '10-15 سم',
                'حجم الحصى': '20 مم',
                'نسبة الماء/الأسمنت': '0.55'
            }),
            'images': json.dumps(['/images/concrete-mix.jpg']),
            'featured': True,
            'category_id': categories['concrete_cement'],
            'supplier_id': suppliers['شركة العمران للمواد']
        },
        
        # حديد وصلب
        {
            'name': 'حديد تسليح قطر 16 مم',
            'description': 'حديد تسليح عالي الجودة قطر 16 مم، طول 12 متر، مطابق للمواصفات السعودية SASO.',
            'price': 45.00,
            'unit': 'عمود',
            'minimum_order': 20,
            'stock_quantity': 500,
            'sku': 'REBAR-16-12M',
            'brand': 'حديد الراجحي',
            'specifications': json.dumps({
                'القطر': '16 مم',
                'الطول': '12 متر',
                'الوزن': '18.96 كيلو/عمود',
                'المقاومة': '420 نيوتن/مم²',
                'المعيار': 'SASO 2532'
            }),
            'images': json.dumps(['/images/rebar-16mm.jpg']),
            'featured': True,
            'category_id': categories['iron_steel'],
            'supplier_id': suppliers['شركة الخليج للحديد']
        },
        {
            'name': 'حديد تسليح قطر 12 مم',
            'description': 'حديد تسليح قطر 12 مم، طول 12 متر، مناسب للبلاطات والجدران غير الحاملة.',
            'price': 28.50,
            'unit': 'عمود',
            'minimum_order': 30,
            'stock_quantity': 800,
            'sku': 'REBAR-12-12M',
            'brand': 'حديد الراجحي',
            'specifications': json.dumps({
                'القطر': '12 مم',
                'الطول': '12 متر',
                'الوزن': '10.67 كيلو/عمود',
                'المقاومة': '420 نيوتن/مم²'
            }),
            'images': json.dumps(['/images/rebar-12mm.jpg']),
            'featured': False,
            'category_id': categories['iron_steel'],
            'supplier_id': suppliers['شركة الخليج للحديد']
        },
        
        # طوب وبلوك
        {
            'name': 'طوب أحمر 25×12×6 سم',
            'description': 'طوب أحمر عالي الجودة مناسب للجدران الخارجية والداخلية، مقاوم للرطوبة والحرارة.',
            'price': 0.85,
            'unit': 'قطعة',
            'minimum_order': 1000,
            'stock_quantity': 50000,
            'sku': 'BRICK-RED-25126',
            'brand': 'طوب الرياض',
            'specifications': json.dumps({
                'الأبعاد': '25×12×6 سم',
                'الوزن': '2.5 كيلو',
                'المقاومة': '15 نيوتن/مم²',
                'امتصاص الماء': 'أقل من 15%'
            }),
            'images': json.dumps(['/images/red-brick.jpg']),
            'featured': True,
            'category_id': categories['brick_block'],
            'supplier_id': suppliers['شركة العمران للمواد']
        },
        
        # عزل
        {
            'name': 'عزل فوم بولي يوريثان 5 سم',
            'description': 'عزل حراري ومائي من الفوم بولي يوريثان، سماكة 5 سم، كثافة عالية.',
            'price': 35.00,
            'unit': 'متر مربع',
            'minimum_order': 50,
            'stock_quantity': 200,
            'sku': 'FOAM-PU-5CM',
            'brand': 'عزل الخليج',
            'specifications': json.dumps({
                'السماكة': '5 سم',
                'الكثافة': '40 كيلو/م³',
                'التوصيل الحراري': '0.025 واط/م.ك',
                'مقاومة الضغط': '300 كيلو باسكال'
            }),
            'images': json.dumps(['/images/foam-insulation.jpg']),
            'featured': True,
            'category_id': categories['insulation'],
            'supplier_id': suppliers['مؤسسة البناء الحديث']
        },
        
        # أبواب ونوافذ
        {
            'name': 'باب خشبي داخلي 80×200 سم',
            'description': 'باب خشبي داخلي من خشب الزان الطبيعي، تشطيب لاكيه، مع الإكسسوارات.',
            'price': 450.00,
            'unit': 'قطعة',
            'minimum_order': 1,
            'stock_quantity': 25,
            'sku': 'DOOR-WOOD-80200',
            'brand': 'أبواب الذهبية',
            'specifications': json.dumps({
                'الأبعاد': '80×200 سم',
                'المادة': 'خشب زان طبيعي',
                'السماكة': '4 سم',
                'التشطيب': 'لاكيه شفاف',
                'الإكسسوارات': 'مقابض ومفصلات'
            }),
            'images': json.dumps(['/images/wooden-door.jpg']),
            'featured': True,
            'category_id': categories['doors_windows'],
            'supplier_id': suppliers['مصنع الأبواب الذهبية']
        },
        
        # سيراميك وبلاط
        {
            'name': 'سيراميك أرضيات 60×60 سم',
            'description': 'سيراميك أرضيات عالي الجودة، مقاوم للانزلاق، مناسب للمناطق الداخلية والخارجية.',
            'price': 25.00,
            'unit': 'متر مربع',
            'minimum_order': 20,
            'stock_quantity': 500,
            'sku': 'CERAMIC-FLOOR-6060',
            'brand': 'سيراميك النجم',
            'specifications': json.dumps({
                'الأبعاد': '60×60 سم',
                'السماكة': '10 مم',
                'امتصاص الماء': 'أقل من 3%',
                'مقاومة الانزلاق': 'R10',
                'التشطيب': 'مات'
            }),
            'images': json.dumps(['/images/ceramic-tiles.jpg']),
            'featured': True,
            'category_id': categories['ceramic_tiles'],
            'supplier_id': suppliers['شركة النجم للسيراميك']
        },
        
        # سباكة
        {
            'name': 'أنبوب PVC قطر 110 مم',
            'description': 'أنبوب PVC للصرف الصحي قطر 110 مم، طول 6 متر، مطابق للمواصفات الدولية.',
            'price': 35.00,
            'unit': 'عمود',
            'minimum_order': 10,
            'stock_quantity': 200,
            'sku': 'PVC-PIPE-110-6M',
            'brand': 'أنابيب الخليج',
            'specifications': json.dumps({
                'القطر': '110 مم',
                'الطول': '6 متر',
                'السماكة': '3.2 مم',
                'الضغط': '6 بار',
                'المعيار': 'ISO 4422'
            }),
            'images': json.dumps(['/images/pvc-pipe.jpg']),
            'featured': False,
            'category_id': categories['plumbing'],
            'supplier_id': suppliers['مؤسسة البناء الحديث']
        },
        
        # كهرباء
        {
            'name': 'كابل كهربائي 2.5 مم² × 100 متر',
            'description': 'كابل كهربائي نحاسي معزول، مقطع 2.5 مم²، طول 100 متر، مناسب للإضاءة والمقابس.',
            'price': 180.00,
            'unit': 'بكرة',
            'minimum_order': 1,
            'stock_quantity': 50,
            'sku': 'CABLE-CU-25-100M',
            'brand': 'كابلات المتقدمة',
            'specifications': json.dumps({
                'المقطع': '2.5 مم²',
                'الطول': '100 متر',
                'المادة': 'نحاس خالص',
                'العزل': 'PVC',
                'الجهد': '450/750 فولت'
            }),
            'images': json.dumps(['/images/electrical-cable.jpg']),
            'featured': True,
            'category_id': categories['electrical'],
            'supplier_id': suppliers['مؤسسة الكهرباء المتقدمة']
        }
    ]
    
    for prod_data in products_data:
        existing = Product.query.filter_by(sku=prod_data['sku']).first()
        if not existing:
            product = Product(**prod_data)
            db.session.add(product)
    
    db.session.commit()
    print("✅ تم إضافة المنتجات بنجاح")

def main():
    """تشغيل جميع دوال إضافة البيانات"""
    with app.app_context():
        print("🚀 بدء إضافة البيانات التجريبية...")
        
        # إضافة الفئات
        seed_categories()
        
        # إضافة الموردين
        seed_suppliers()
        
        # إضافة المنتجات
        seed_products()
        
        print("✅ تم إضافة جميع البيانات التجريبية بنجاح!")
        print(f"📊 إحصائيات:")
        print(f"   - الفئات: {Category.query.count()}")
        print(f"   - الموردين: {Supplier.query.count()}")
        print(f"   - المنتجات: {Product.query.count()}")

if __name__ == '__main__':
    main()

