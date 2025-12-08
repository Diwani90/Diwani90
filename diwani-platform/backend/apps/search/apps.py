"""
===================================
منصة ديواني - Search App Config
===================================
"""

import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class SearchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.search'
    verbose_name = 'البحث المتقدم'

    def ready(self):
        """تحميل الإشارات وإعداد Elasticsearch عند بدء التطبيق"""
        # تحميل الإشارات
        try:
            import apps.search.signals  # noqa
        except ImportError:
            pass

        # إنشاء فهارس Elasticsearch تلقائياً
        self._setup_elasticsearch_indexes()

    def _setup_elasticsearch_indexes(self):
        """إنشاء فهارس Elasticsearch إذا لم تكن موجودة"""
        import os
        import sys

        # تجنب التنفيذ في migrate, collectstatic, إلخ
        if len(sys.argv) > 1 and sys.argv[1] in ['migrate', 'collectstatic', 'makemigrations', 'shell', 'test']:
            return

        # تجنب التنفيذ المتكرر في runserver (المرة الثانية فقط)
        if 'runserver' in sys.argv and os.environ.get('RUN_MAIN') != 'true':
            return

        from django.conf import settings

        # التحقق من تفعيل Elasticsearch
        if not getattr(settings, 'ELASTICSEARCH_ENABLED', True):
            logger.info("Elasticsearch disabled, skipping index setup")
            return

        try:
            from .documents import (
                setup_elasticsearch_connection,
                ProductDocument,
                StoreDocument,
                CategoryDocument,
                VendorDocument
            )

            # إعداد الاتصال
            setup_elasticsearch_connection()

            # إنشاء الفهارس إذا لم تكن موجودة
            for doc_class in [ProductDocument, StoreDocument, CategoryDocument, VendorDocument]:
                index = doc_class._index
                try:
                    if not index.exists():
                        index.create()
                        logger.info(f"Created Elasticsearch index: {index._name}")
                    else:
                        logger.debug(f"Elasticsearch index exists: {index._name}")
                except Exception as e:
                    logger.warning(f"Could not create index {index._name}: {e}")

            logger.info("Elasticsearch indexes setup completed")

        except Exception as e:
            logger.warning(f"Elasticsearch setup skipped: {e}")
