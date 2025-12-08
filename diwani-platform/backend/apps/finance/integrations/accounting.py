"""
تكامل برامج المحاسبة
====================

الربط مع قيود / دفاتر للفوترة الإلكترونية ZATCA
المنصة تراقب وتسجل، برنامج المحاسبة يتولى ZATCA
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class AccountingProvider(Enum):
    """مزودي خدمات المحاسبة"""
    QOYOD = 'qoyod'
    DAFATER = 'dafater'
    CUSTOM = 'custom'


class InvoiceStatus(Enum):
    """حالات الفاتورة"""
    DRAFT = 'draft'
    PENDING = 'pending'
    SUBMITTED = 'submitted'
    CLEARED = 'cleared'
    REPORTED = 'reported'
    REJECTED = 'rejected'


@dataclass
class AccountingInvoice:
    """بيانات الفاتورة للمحاسبة"""
    invoice_number: str
    invoice_date: datetime
    due_date: Optional[datetime]
    vendor_name: str
    vendor_vat: Optional[str]
    vendor_cr: Optional[str]
    customer_name: str
    customer_vat: Optional[str]
    customer_phone: Optional[str]
    line_items: List[Dict[str, Any]]
    subtotal: Decimal
    tax_amount: Decimal
    total: Decimal
    currency: str = 'SAR'
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AccountingProviderInterface(ABC):
    """واجهة مزود المحاسبة"""

    @abstractmethod
    def authenticate(self) -> bool:
        """التحقق من صحة الاتصال"""
        pass

    @abstractmethod
    def create_invoice(self, invoice: AccountingInvoice) -> Dict[str, Any]:
        """إنشاء فاتورة"""
        pass

    @abstractmethod
    def get_invoice_status(self, invoice_id: str) -> Dict[str, Any]:
        """حالة الفاتورة وZATCA"""
        pass

    @abstractmethod
    def sync_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """مزامنة حالة الفاتورة"""
        pass

    @abstractmethod
    def get_zatca_qr(self, invoice_id: str) -> Optional[str]:
        """الحصول على QR Code من ZATCA"""
        pass


class QoyodProvider(AccountingProviderInterface):
    """
    تكامل منصة قيود المحاسبية

    قيود يتولى:
    - إنشاء الفواتير الإلكترونية
    - الربط مع ZATCA
    - إدارة QR Codes
    """

    def __init__(self):
        self.api_key = getattr(settings, 'QOYOD_API_KEY', '')
        self.organization_id = getattr(settings, 'QOYOD_ORGANIZATION_ID', '')
        self.base_url = 'https://api.qoyod.com/v1/'
        self.timeout = 30
        self._session = None

    @property
    def session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'X-Organization-Id': self.organization_id,
                'Content-Type': 'application/json',
            })
        return self._session

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """إجراء طلب API"""
        url = urljoin(self.base_url, endpoint)

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Qoyod API error: {e}")
            raise

    def authenticate(self) -> bool:
        """التحقق من صحة الاتصال"""
        try:
            response = self._make_request('GET', 'organization')
            return response.get('status') == 'active'
        except Exception:
            return False

    def create_invoice(self, invoice: AccountingInvoice) -> Dict[str, Any]:
        """إنشاء فاتورة في قيود"""
        line_items = []
        for item in invoice.line_items:
            line_items.append({
                'description': item.get('name'),
                'quantity': item.get('quantity'),
                'unit_price': float(item.get('price')),
                'tax_rate': 15.0,  # VAT السعودية
            })

        data = {
            'invoice_number': invoice.invoice_number,
            'invoice_date': invoice.invoice_date.strftime('%Y-%m-%d'),
            'due_date': invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else None,
            'customer': {
                'name': invoice.customer_name,
                'vat_number': invoice.customer_vat,
                'phone': invoice.customer_phone,
            },
            'line_items': line_items,
            'notes': invoice.notes,
            'submit_to_zatca': True,  # تقديم تلقائي لـ ZATCA
        }

        logger.info(f"Creating invoice in Qoyod: {invoice.invoice_number}")
        response = self._make_request('POST', 'invoices', data=data)

        return {
            'provider': 'qoyod',
            'provider_invoice_id': response.get('id'),
            'status': response.get('status'),
            'zatca_status': response.get('zatca_status'),
            'created_at': response.get('created_at'),
        }

    def get_invoice_status(self, invoice_id: str) -> Dict[str, Any]:
        """حالة الفاتورة"""
        response = self._make_request('GET', f'invoices/{invoice_id}')

        return {
            'invoice_id': invoice_id,
            'status': response.get('status'),
            'zatca_status': response.get('zatca_status'),
            'zatca_clearance_status': response.get('zatca_clearance_status'),
            'zatca_invoice_hash': response.get('zatca_invoice_hash'),
        }

    def sync_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """مزامنة حالة الفاتورة مع ZATCA"""
        return self._make_request('POST', f'invoices/{invoice_id}/sync-zatca')

    def get_zatca_qr(self, invoice_id: str) -> Optional[str]:
        """الحصول على QR Code"""
        response = self._make_request('GET', f'invoices/{invoice_id}/qr')
        return response.get('qr_code')


class DafaterProvider(AccountingProviderInterface):
    """
    تكامل منصة دفاتر المحاسبية

    بديل لقيود مع نفس الوظائف
    """

    def __init__(self):
        self.api_key = getattr(settings, 'DAFATER_API_KEY', '')
        self.base_url = 'https://api.dafater.sa/v1/'
        self.timeout = 30
        self._session = None

    @property
    def session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                'X-API-Key': self.api_key,
                'Content-Type': 'application/json',
            })
        return self._session

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """إجراء طلب API"""
        url = urljoin(self.base_url, endpoint)

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Dafater API error: {e}")
            raise

    def authenticate(self) -> bool:
        """التحقق من صحة الاتصال"""
        try:
            response = self._make_request('GET', 'account')
            return response.get('active', False)
        except Exception:
            return False

    def create_invoice(self, invoice: AccountingInvoice) -> Dict[str, Any]:
        """إنشاء فاتورة في دفاتر"""
        items = []
        for item in invoice.line_items:
            items.append({
                'item_name': item.get('name'),
                'qty': item.get('quantity'),
                'price': float(item.get('price')),
                'vat_percent': 15,
            })

        data = {
            'number': invoice.invoice_number,
            'date': invoice.invoice_date.strftime('%Y-%m-%d'),
            'client_name': invoice.customer_name,
            'client_vat': invoice.customer_vat,
            'client_mobile': invoice.customer_phone,
            'items': items,
            'auto_zatca': True,
        }

        logger.info(f"Creating invoice in Dafater: {invoice.invoice_number}")
        response = self._make_request('POST', 'invoices', data=data)

        return {
            'provider': 'dafater',
            'provider_invoice_id': response.get('invoice_id'),
            'status': response.get('status'),
            'zatca_status': response.get('zatca', {}).get('status'),
            'created_at': response.get('created_at'),
        }

    def get_invoice_status(self, invoice_id: str) -> Dict[str, Any]:
        """حالة الفاتورة"""
        response = self._make_request('GET', f'invoices/{invoice_id}')

        return {
            'invoice_id': invoice_id,
            'status': response.get('status'),
            'zatca_status': response.get('zatca', {}).get('status'),
            'zatca_hash': response.get('zatca', {}).get('hash'),
        }

    def sync_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """مزامنة مع ZATCA"""
        return self._make_request('POST', f'invoices/{invoice_id}/zatca/sync')

    def get_zatca_qr(self, invoice_id: str) -> Optional[str]:
        """QR Code"""
        response = self._make_request('GET', f'invoices/{invoice_id}/qr')
        return response.get('data')


class AccountingSyncService:
    """
    خدمة مزامنة المحاسبة

    نحن نراقب ونسجل، برنامج المحاسبة يتولى ZATCA
    """

    def __init__(self, provider: Optional[AccountingProvider] = None):
        self.provider_type = provider or AccountingProvider(
            getattr(settings, 'ACCOUNTING_PROVIDER', 'qoyod')
        )
        self._provider = None

    @property
    def provider(self) -> AccountingProviderInterface:
        """الحصول على مزود المحاسبة"""
        if self._provider is None:
            if self.provider_type == AccountingProvider.QOYOD:
                self._provider = QoyodProvider()
            elif self.provider_type == AccountingProvider.DAFATER:
                self._provider = DafaterProvider()
            else:
                raise ValueError(f"Unsupported provider: {self.provider_type}")
        return self._provider

    def sync_order_invoice(
        self,
        order_id: str,
        invoice_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        مزامنة فاتورة الطلب مع برنامج المحاسبة

        الخطوات:
        1. إنشاء الفاتورة في برنامج المحاسبة
        2. برنامج المحاسبة يرسل لـ ZATCA
        3. نحفظ المرجع والحالة
        """
        try:
            # تحويل البيانات لصيغة AccountingInvoice
            invoice = AccountingInvoice(
                invoice_number=invoice_data.get('invoice_number'),
                invoice_date=datetime.fromisoformat(invoice_data.get('invoice_date')),
                due_date=None,
                vendor_name=invoice_data.get('vendor', {}).get('name'),
                vendor_vat=invoice_data.get('vendor', {}).get('vat_number'),
                vendor_cr=invoice_data.get('vendor', {}).get('cr_number'),
                customer_name=invoice_data.get('customer', {}).get('name'),
                customer_vat=invoice_data.get('customer', {}).get('vat_number'),
                customer_phone=invoice_data.get('customer', {}).get('phone'),
                line_items=invoice_data.get('line_items', []),
                subtotal=Decimal(str(invoice_data.get('subtotal', 0))),
                tax_amount=Decimal(str(invoice_data.get('tax_amount', 0))),
                total=Decimal(str(invoice_data.get('total', 0))),
                metadata={'order_id': order_id}
            )

            # إرسال لبرنامج المحاسبة
            result = self.provider.create_invoice(invoice)

            logger.info(f"Invoice synced for order {order_id}: {result}")

            return {
                'success': True,
                'order_id': order_id,
                'accounting_provider': self.provider_type.value,
                **result
            }

        except Exception as e:
            logger.error(f"Failed to sync invoice for order {order_id}: {e}")
            return {
                'success': False,
                'order_id': order_id,
                'error': str(e),
            }

    def get_zatca_status(
        self,
        provider_invoice_id: str
    ) -> Dict[str, Any]:
        """
        الحصول على حالة ZATCA من برنامج المحاسبة
        """
        try:
            status = self.provider.get_invoice_status(provider_invoice_id)
            qr_code = self.provider.get_zatca_qr(provider_invoice_id)

            return {
                'success': True,
                **status,
                'qr_code': qr_code,
            }

        except Exception as e:
            logger.error(f"Failed to get ZATCA status: {e}")
            return {
                'success': False,
                'error': str(e),
            }

    def sync_pending_invoices(self) -> Dict[str, Any]:
        """
        مزامنة الفواتير المعلقة

        تُستدعى من Celery task
        """
        from ..models import Invoice

        pending = Invoice.objects.filter(
            zatca_status='pending'
        ).select_related('order')

        results = {
            'synced': 0,
            'failed': 0,
            'errors': []
        }

        for invoice in pending:
            try:
                if invoice.accounting_provider_id:
                    # مزامنة الحالة فقط
                    status = self.provider.sync_invoice(invoice.accounting_provider_id)

                    invoice.zatca_status = status.get('zatca_status', 'pending')
                    if status.get('qr_code'):
                        invoice.zatca_qr_code = status['qr_code']

                    invoice.save(update_fields=['zatca_status', 'zatca_qr_code', 'updated_at'])
                    results['synced'] += 1

            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'invoice_id': str(invoice.id),
                    'error': str(e)
                })

        return results


# Singleton instance
accounting_sync = AccountingSyncService()
