"""
===================================
منصة ديواني - Setup Elasticsearch Command
أمر إعداد Elasticsearch
===================================

الاستخدام:
    python manage.py setup_elasticsearch
    python manage.py setup_elasticsearch --force  # إعادة إنشاء الفهارس
    python manage.py setup_elasticsearch --index products  # فهرس محدد
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

import time


class Command(BaseCommand):
    help = 'إعداد فهارس Elasticsearch وإنشاؤها'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='حذف الفهارس الموجودة وإعادة إنشائها',
        )
        parser.add_argument(
            '--index',
            type=str,
            choices=['products', 'stores', 'categories', 'vendors', 'all'],
            default='all',
            help='الفهرس المراد إنشاؤه (الافتراضي: all)',
        )
        parser.add_argument(
            '--no-data',
            action='store_true',
            help='إنشاء الفهارس فقط بدون فهرسة البيانات',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('🔧 بدء إعداد Elasticsearch...'))

        # التحقق من الإعدادات
        if not self._check_settings():
            raise CommandError('إعدادات Elasticsearch غير موجودة')

        # إعداد الاتصال
        if not self._setup_connection():
            raise CommandError('فشل الاتصال بـ Elasticsearch')

        # إنشاء الفهارس
        index_name = options['index']
        force = options['force']
        no_data = options['no_data']

        indexes = self._get_indexes(index_name)

        for idx_name, idx_class in indexes.items():
            self._create_index(idx_name, idx_class, force)

        # فهرسة البيانات
        if not no_data:
            self.stdout.write(self.style.NOTICE('\n📦 بدء فهرسة البيانات...'))
            self._index_data(index_name)

        self.stdout.write(self.style.SUCCESS('\n✅ تم إعداد Elasticsearch بنجاح!'))

    def _check_settings(self) -> bool:
        """التحقق من إعدادات Elasticsearch"""
        es_config = getattr(settings, 'ELASTICSEARCH_DSL', None)
        if not es_config:
            self.stdout.write(self.style.WARNING(
                '⚠️ ELASTICSEARCH_DSL غير موجود في الإعدادات\n'
                'سيتم استخدام الإعدادات الافتراضية: http://localhost:9200'
            ))
        return True

    def _setup_connection(self) -> bool:
        """إعداد الاتصال بـ Elasticsearch"""
        try:
            from apps.search.documents import setup_elasticsearch_connection
            from elasticsearch_dsl import connections

            setup_elasticsearch_connection()
            es = connections.get_connection()

            # التحقق من الاتصال
            if es.ping():
                info = es.info()
                self.stdout.write(self.style.SUCCESS(
                    f'✅ متصل بـ Elasticsearch {info["version"]["number"]}'
                ))
                return True
            else:
                self.stdout.write(self.style.ERROR('❌ فشل الاتصال بـ Elasticsearch'))
                return False

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ خطأ في الاتصال: {e}'))
            return False

    def _get_indexes(self, index_name: str) -> dict:
        """الحصول على الفهارس المطلوبة"""
        from apps.search.documents import (
            ProductDocument, StoreDocument,
            CategoryDocument, VendorDocument
        )

        all_indexes = {
            'products': ProductDocument,
            'stores': StoreDocument,
            'categories': CategoryDocument,
            'vendors': VendorDocument,
        }

        if index_name == 'all':
            return all_indexes
        elif index_name in all_indexes:
            return {index_name: all_indexes[index_name]}
        else:
            raise CommandError(f'فهرس غير معروف: {index_name}')

    def _create_index(self, name: str, doc_class, force: bool):
        """إنشاء فهرس"""
        index = doc_class._index

        if index.exists():
            if force:
                self.stdout.write(f'🗑️ حذف الفهرس: {index._name}')
                index.delete()
            else:
                self.stdout.write(self.style.WARNING(
                    f'⚠️ الفهرس موجود: {index._name} (استخدم --force للحذف)'
                ))
                return

        self.stdout.write(f'📝 إنشاء الفهرس: {index._name}')
        index.create()
        self.stdout.write(self.style.SUCCESS(f'✅ تم إنشاء: {index._name}'))

    def _index_data(self, index_name: str):
        """فهرسة البيانات"""
        if index_name in ['all', 'products']:
            self._index_products()

        if index_name in ['all', 'stores']:
            self._index_stores()

        if index_name in ['all', 'categories']:
            self._index_categories()

        if index_name in ['all', 'vendors']:
            self._index_vendors()

    def _index_products(self):
        """فهرسة المنتجات"""
        try:
            from apps.products.models import Product
            from apps.search.documents import ProductDocument

            products = Product.objects.filter(status='active').select_related(
                'category', 'store', 'store__vendor'
            ).prefetch_related('images', 'variants')

            total = products.count()
            self.stdout.write(f'📦 فهرسة {total} منتج...')

            indexed = 0
            errors = 0
            start_time = time.time()

            for product in products.iterator(chunk_size=100):
                try:
                    doc = ProductDocument.from_django_model(product)
                    doc.save()
                    indexed += 1

                    if indexed % 100 == 0:
                        self.stdout.write(f'  تم فهرسة {indexed}/{total}')

                except Exception as e:
                    errors += 1
                    self.stdout.write(self.style.WARNING(
                        f'  ⚠️ خطأ في المنتج {product.id}: {e}'
                    ))

            elapsed = time.time() - start_time
            self.stdout.write(self.style.SUCCESS(
                f'  ✅ تم فهرسة {indexed} منتج ({errors} أخطاء) في {elapsed:.2f} ثانية'
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ خطأ في فهرسة المنتجات: {e}'))

    def _index_stores(self):
        """فهرسة المتاجر"""
        try:
            from apps.stores.models import Store
            from apps.search.documents import StoreDocument

            stores = Store.objects.filter(status='active').select_related(
                'category', 'vendor'
            ).prefetch_related('products')

            total = stores.count()
            self.stdout.write(f'🏪 فهرسة {total} متجر...')

            indexed = 0
            for store in stores.iterator(chunk_size=50):
                try:
                    doc = StoreDocument.from_django_model(store)
                    doc.save()
                    indexed += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(
                        f'  ⚠️ خطأ في المتجر {store.id}: {e}'
                    ))

            self.stdout.write(self.style.SUCCESS(f'  ✅ تم فهرسة {indexed} متجر'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ خطأ في فهرسة المتاجر: {e}'))

    def _index_categories(self):
        """فهرسة التصنيفات"""
        try:
            from apps.products.models import ProductCategory
            from apps.search.documents import CategoryDocument

            categories = ProductCategory.objects.filter(is_active=True)
            total = categories.count()
            self.stdout.write(f'📁 فهرسة {total} تصنيف...')

            indexed = 0
            for cat in categories.iterator():
                try:
                    doc = CategoryDocument(meta={'id': cat.id})
                    doc.id = cat.id
                    doc.name = cat.name
                    doc.name_en = getattr(cat, 'name_en', '')
                    doc.slug = cat.slug
                    doc.description = getattr(cat, 'description', '')
                    doc.is_active = cat.is_active
                    doc.products_count = cat.products.filter(status='active').count()

                    if cat.parent:
                        doc.parent_id = cat.parent.id
                        doc.parent_name = cat.parent.name

                    doc.save()
                    indexed += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(
                        f'  ⚠️ خطأ في التصنيف {cat.id}: {e}'
                    ))

            self.stdout.write(self.style.SUCCESS(f'  ✅ تم فهرسة {indexed} تصنيف'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ خطأ في فهرسة التصنيفات: {e}'))

    def _index_vendors(self):
        """فهرسة الموردين"""
        try:
            from apps.accounts.models import VendorProfile
            from apps.search.documents import VendorDocument

            vendors = VendorProfile.objects.filter(is_verified=True)
            total = vendors.count()
            self.stdout.write(f'🏭 فهرسة {total} مورد...')

            indexed = 0
            for vendor in vendors.iterator():
                try:
                    doc = VendorDocument(meta={'id': vendor.id})
                    doc.id = vendor.id
                    doc.company_name = vendor.company_name
                    doc.commercial_register = vendor.commercial_register
                    doc.is_verified = vendor.is_verified
                    doc.status = vendor.status
                    doc.created_at = vendor.created_at

                    doc.save()
                    indexed += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(
                        f'  ⚠️ خطأ في المورد {vendor.id}: {e}'
                    ))

            self.stdout.write(self.style.SUCCESS(f'  ✅ تم فهرسة {indexed} مورد'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ خطأ في فهرسة الموردين: {e}'))
