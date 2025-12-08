"""
===================================
منصة ديواني - Rebuild Index Command
أمر إعادة بناء فهارس البحث
===================================

الاستخدام:
    python manage.py rebuild_index
    python manage.py rebuild_index --index products
    python manage.py rebuild_index --async  # استخدام Celery
    python manage.py rebuild_index --batch-size 200
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import time


class Command(BaseCommand):
    help = 'إعادة بناء فهارس Elasticsearch من البيانات الموجودة'

    def add_arguments(self, parser):
        parser.add_argument(
            '--index',
            type=str,
            choices=['products', 'stores', 'categories', 'vendors', 'all'],
            default='all',
            help='الفهرس المراد إعادة بنائه',
        )
        parser.add_argument(
            '--async',
            action='store_true',
            dest='use_async',
            help='استخدام Celery للفهرسة غير المتزامنة',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='حجم الدفعة للفهرسة',
        )
        parser.add_argument(
            '--no-delete',
            action='store_true',
            help='عدم حذف الفهرس قبل إعادة البناء',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('🔄 بدء إعادة بناء الفهارس...'))

        index_name = options['index']
        use_async = options['use_async']
        batch_size = options['batch_size']
        no_delete = options['no_delete']

        # إعداد الاتصال
        from apps.search.documents import setup_elasticsearch_connection
        setup_elasticsearch_connection()

        if use_async:
            self._rebuild_async(index_name)
        else:
            self._rebuild_sync(index_name, batch_size, no_delete)

        self.stdout.write(self.style.SUCCESS('\n✅ تمت إعادة بناء الفهارس!'))

    def _rebuild_async(self, index_name: str):
        """إعادة البناء باستخدام Celery"""
        from apps.search.tasks import (
            full_reindex_products_task,
            full_reindex_stores_task,
            full_reindex_all_task
        )

        if index_name == 'all':
            self.stdout.write('📤 إرسال مهمة إعادة بناء جميع الفهارس...')
            full_reindex_all_task.delay()
        elif index_name == 'products':
            self.stdout.write('📤 إرسال مهمة إعادة بناء فهرس المنتجات...')
            full_reindex_products_task.delay()
        elif index_name == 'stores':
            self.stdout.write('📤 إرسال مهمة إعادة بناء فهرس المتاجر...')
            full_reindex_stores_task.delay()
        else:
            self.stdout.write(self.style.WARNING(
                f'⚠️ الفهرس {index_name} لا يدعم الفهرسة غير المتزامنة'
            ))

        self.stdout.write(self.style.SUCCESS('✅ تم إرسال المهام إلى Celery'))

    def _rebuild_sync(self, index_name: str, batch_size: int, no_delete: bool):
        """إعادة البناء المتزامنة"""
        from elasticsearch.helpers import bulk
        from elasticsearch_dsl import connections

        es = connections.get_connection()

        if index_name in ['all', 'products']:
            self._rebuild_products(es, batch_size, no_delete)

        if index_name in ['all', 'stores']:
            self._rebuild_stores(es, batch_size, no_delete)

        if index_name in ['all', 'categories']:
            self._rebuild_categories(es, batch_size, no_delete)

        if index_name in ['all', 'vendors']:
            self._rebuild_vendors(es, batch_size, no_delete)

    def _rebuild_products(self, es, batch_size: int, no_delete: bool):
        """إعادة بناء فهرس المنتجات"""
        from apps.products.models import Product
        from apps.search.documents import ProductDocument
        from elasticsearch.helpers import bulk

        index_name = ProductDocument._index._name

        # حذف وإعادة إنشاء الفهرس
        if not no_delete:
            self.stdout.write(f'🗑️ حذف الفهرس: {index_name}')
            ProductDocument._index.delete(ignore=404)
            ProductDocument._index.create()
            self.stdout.write(f'📝 تم إنشاء الفهرس: {index_name}')

        # فهرسة البيانات
        products = Product.objects.filter(status='active').select_related(
            'category', 'store', 'store__vendor'
        ).prefetch_related('images', 'variants')

        total = products.count()
        self.stdout.write(f'📦 فهرسة {total} منتج (دفعات: {batch_size})...')

        start_time = time.time()
        indexed = 0
        failed = 0

        def generate_actions():
            nonlocal indexed, failed
            for product in products.iterator(chunk_size=batch_size):
                try:
                    doc = ProductDocument.from_django_model(product)
                    yield doc.to_dict(include_meta=True)
                    indexed += 1
                except Exception as e:
                    failed += 1
                    self.stdout.write(self.style.WARNING(
                        f'  ⚠️ خطأ في المنتج {product.id}: {e}'
                    ))

        # فهرسة مجمعة
        success, errors = bulk(
            es,
            generate_actions(),
            chunk_size=batch_size,
            raise_on_error=False,
            raise_on_exception=False
        )

        elapsed = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(
            f'  ✅ المنتجات: {success} نجاح, {len(errors)} فشل ({elapsed:.2f}s)'
        ))

    def _rebuild_stores(self, es, batch_size: int, no_delete: bool):
        """إعادة بناء فهرس المتاجر"""
        from apps.stores.models import Store
        from apps.search.documents import StoreDocument
        from elasticsearch.helpers import bulk

        index_name = StoreDocument._index._name

        if not no_delete:
            self.stdout.write(f'🗑️ حذف الفهرس: {index_name}')
            StoreDocument._index.delete(ignore=404)
            StoreDocument._index.create()

        stores = Store.objects.filter(status='active').select_related(
            'category', 'vendor'
        ).prefetch_related('products')

        total = stores.count()
        self.stdout.write(f'🏪 فهرسة {total} متجر...')

        start_time = time.time()

        def generate_actions():
            for store in stores.iterator(chunk_size=batch_size):
                try:
                    doc = StoreDocument.from_django_model(store)
                    yield doc.to_dict(include_meta=True)
                except Exception as e:
                    self.stdout.write(self.style.WARNING(
                        f'  ⚠️ خطأ في المتجر {store.id}: {e}'
                    ))

        success, errors = bulk(
            es,
            generate_actions(),
            chunk_size=batch_size,
            raise_on_error=False
        )

        elapsed = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(
            f'  ✅ المتاجر: {success} نجاح ({elapsed:.2f}s)'
        ))

    def _rebuild_categories(self, es, batch_size: int, no_delete: bool):
        """إعادة بناء فهرس التصنيفات"""
        from apps.products.models import ProductCategory
        from apps.search.documents import CategoryDocument
        from elasticsearch.helpers import bulk

        index_name = CategoryDocument._index._name

        if not no_delete:
            CategoryDocument._index.delete(ignore=404)
            CategoryDocument._index.create()

        categories = ProductCategory.objects.filter(is_active=True)
        total = categories.count()
        self.stdout.write(f'📁 فهرسة {total} تصنيف...')

        def generate_actions():
            for cat in categories.iterator():
                doc = CategoryDocument(meta={'id': cat.id})
                doc.id = cat.id
                doc.name = cat.name
                doc.name_en = getattr(cat, 'name_en', '')
                doc.slug = cat.slug
                doc.is_active = True
                doc.products_count = cat.products.filter(status='active').count()

                if cat.parent:
                    doc.parent_id = cat.parent.id
                    doc.parent_name = cat.parent.name

                yield doc.to_dict(include_meta=True)

        success, _ = bulk(es, generate_actions(), raise_on_error=False)
        self.stdout.write(self.style.SUCCESS(f'  ✅ التصنيفات: {success} نجاح'))

    def _rebuild_vendors(self, es, batch_size: int, no_delete: bool):
        """إعادة بناء فهرس الموردين"""
        from apps.accounts.models import VendorProfile
        from apps.search.documents import VendorDocument
        from elasticsearch.helpers import bulk

        index_name = VendorDocument._index._name

        if not no_delete:
            VendorDocument._index.delete(ignore=404)
            VendorDocument._index.create()

        vendors = VendorProfile.objects.filter(is_verified=True)
        total = vendors.count()
        self.stdout.write(f'🏭 فهرسة {total} مورد...')

        def generate_actions():
            for vendor in vendors.iterator():
                doc = VendorDocument(meta={'id': vendor.id})
                doc.id = vendor.id
                doc.company_name = vendor.company_name
                doc.is_verified = vendor.is_verified
                doc.status = vendor.status
                doc.created_at = vendor.created_at

                yield doc.to_dict(include_meta=True)

        success, _ = bulk(es, generate_actions(), raise_on_error=False)
        self.stdout.write(self.style.SUCCESS(f'  ✅ الموردين: {success} نجاح'))
