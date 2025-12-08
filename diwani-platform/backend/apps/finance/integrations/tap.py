"""
تكامل Tap Payments
==================

Tap Connect للأسواق متعددة البائعين
يتولى Tap حساب وتقسيم العمولات تلقائياً
"""

import hashlib
import hmac
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class TapEnvironment(Enum):
    """بيئات Tap"""
    SANDBOX = 'sandbox'
    PRODUCTION = 'production'


class TapPaymentStatus(Enum):
    """حالات الدفع"""
    INITIATED = 'INITIATED'
    AUTHORIZED = 'AUTHORIZED'
    CAPTURED = 'CAPTURED'
    REFUNDED = 'REFUNDED'
    VOID = 'VOID'
    FAILED = 'FAILED'
    CANCELLED = 'CANCELLED'


class TapTransferStatus(Enum):
    """حالات التحويل"""
    PENDING = 'pending'
    IN_TRANSIT = 'in_transit'
    PAID = 'paid'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


@dataclass
class TapDestination:
    """وجهة التحويل (تاجر أو سائق)"""
    id: str  # Tap Connect Account ID
    amount: Decimal
    currency: str = 'SAR'
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'amount': float(self.amount),
            'currency': self.currency,
            'description': self.description,
        }


@dataclass
class TapPaymentRequest:
    """طلب دفع جديد"""
    amount: Decimal
    currency: str
    customer_id: Optional[str]
    customer_email: Optional[str]
    customer_phone: str
    description: str
    reference_id: str  # Order ID
    destinations: List[TapDestination]
    redirect_url: str
    post_url: str  # Webhook URL
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        data = {
            'amount': float(self.amount),
            'currency': self.currency,
            'customer': {},
            'source': {'id': 'src_all'},  # قبول جميع طرق الدفع
            'redirect': {'url': self.redirect_url},
            'post': {'url': self.post_url},
            'description': self.description,
            'reference': {'transaction': self.reference_id},
            'destinations': {
                'destination': [d.to_dict() for d in self.destinations]
            },
            'metadata': self.metadata or {},
        }

        if self.customer_id:
            data['customer']['id'] = self.customer_id
        if self.customer_email:
            data['customer']['email'] = self.customer_email
        if self.customer_phone:
            data['customer']['phone'] = {
                'country_code': '966',
                'number': self.customer_phone.lstrip('+966').lstrip('0')
            }

        return data


@dataclass
class TapPaymentResponse:
    """استجابة الدفع"""
    id: str
    status: TapPaymentStatus
    amount: Decimal
    currency: str
    reference_id: str
    payment_url: Optional[str]
    transaction_url: Optional[str]
    created_at: datetime
    raw_response: Dict[str, Any]

    @classmethod
    def from_response(cls, data: Dict[str, Any]) -> 'TapPaymentResponse':
        return cls(
            id=data.get('id', ''),
            status=TapPaymentStatus(data.get('status', 'INITIATED')),
            amount=Decimal(str(data.get('amount', 0))),
            currency=data.get('currency', 'SAR'),
            reference_id=data.get('reference', {}).get('transaction', ''),
            payment_url=data.get('transaction', {}).get('url'),
            transaction_url=data.get('transaction', {}).get('url'),
            created_at=datetime.fromisoformat(
                data.get('transaction', {}).get('created', timezone.now().isoformat())
            ),
            raw_response=data,
        )


class TapConnectClient:
    """
    عميل Tap Connect API

    يدير:
    - إنشاء حسابات البائعين (Connected Accounts)
    - معالجة المدفوعات مع التقسيم التلقائي
    - استرجاع بيانات التسوية
    - Webhooks
    """

    BASE_URLS = {
        TapEnvironment.SANDBOX: 'https://api.tap.company/v2/',
        TapEnvironment.PRODUCTION: 'https://api.tap.company/v2/',
    }

    def __init__(self):
        self.environment = TapEnvironment(
            getattr(settings, 'TAP_ENVIRONMENT', 'sandbox')
        )
        self.secret_key = getattr(settings, 'TAP_SECRET_KEY', '')
        self.public_key = getattr(settings, 'TAP_PUBLIC_KEY', '')
        self.webhook_secret = getattr(settings, 'TAP_WEBHOOK_SECRET', '')
        self.base_url = self.BASE_URLS[self.environment]
        self.timeout = 30
        self._session = None

    @property
    def session(self) -> requests.Session:
        """إنشاء أو إعادة استخدام الجلسة"""
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                'Authorization': f'Bearer {self.secret_key}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            })
        return self._session

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        retry_count: int = 3
    ) -> Dict[str, Any]:
        """إجراء طلب HTTP مع إعادة المحاولة"""
        url = urljoin(self.base_url, endpoint)

        for attempt in range(retry_count):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    timeout=self.timeout
                )

                response.raise_for_status()
                return response.json()

            except requests.exceptions.Timeout:
                logger.warning(f"Tap API timeout (attempt {attempt + 1}/{retry_count})")
                if attempt == retry_count - 1:
                    raise

            except requests.exceptions.HTTPError as e:
                logger.error(f"Tap API error: {e.response.status_code} - {e.response.text}")
                if e.response.status_code >= 500 and attempt < retry_count - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise

            except requests.exceptions.RequestException as e:
                logger.error(f"Tap API request failed: {e}")
                raise

        return {}

    # =====================================
    # Connected Accounts (حسابات البائعين)
    # =====================================

    def create_connected_account(
        self,
        name: str,
        email: str,
        phone: str,
        iban: str,
        bank_name: str,
        business_type: str = 'individual',
        cr_number: Optional[str] = None,
        vat_number: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        إنشاء حساب متصل جديد (تاجر أو سائق)

        يستخدم لاستقبال المدفوعات المقسمة
        """
        data = {
            'type': business_type,
            'name': name,
            'email': email,
            'phone': {
                'country_code': '966',
                'number': phone.lstrip('+966').lstrip('0')
            },
            'bank': {
                'iban': iban,
                'name': bank_name,
            },
            'metadata': metadata or {},
        }

        if cr_number:
            data['legal_entity'] = data.get('legal_entity', {})
            data['legal_entity']['cr_number'] = cr_number

        if vat_number:
            data['legal_entity'] = data.get('legal_entity', {})
            data['legal_entity']['vat_number'] = vat_number

        logger.info(f"Creating Tap connected account for: {name}")
        response = self._make_request('POST', 'connect/accounts', data=data)

        return {
            'tap_account_id': response.get('id'),
            'status': response.get('status'),
            'created_at': response.get('created'),
            'raw': response,
        }

    def get_connected_account(self, account_id: str) -> Dict[str, Any]:
        """استرجاع تفاصيل حساب متصل"""
        return self._make_request('GET', f'connect/accounts/{account_id}')

    def update_connected_account(
        self,
        account_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """تحديث بيانات حساب متصل"""
        return self._make_request('PUT', f'connect/accounts/{account_id}', data=updates)

    def list_connected_accounts(
        self,
        limit: int = 25,
        starting_after: Optional[str] = None
    ) -> Dict[str, Any]:
        """قائمة الحسابات المتصلة"""
        params = {'limit': limit}
        if starting_after:
            params['starting_after'] = starting_after

        return self._make_request('GET', 'connect/accounts', params=params)

    # =====================================
    # المدفوعات والتقسيم
    # =====================================

    def create_payment(self, request: TapPaymentRequest) -> TapPaymentResponse:
        """
        إنشاء عملية دفع جديدة مع تقسيم تلقائي

        Tap يتولى:
        1. معالجة الدفع من العميل
        2. خصم عمولتنا (تُحدد في لوحة Tap)
        3. تحويل المبالغ للوجهات المحددة
        """
        logger.info(f"Creating Tap payment for order: {request.reference_id}")

        response = self._make_request('POST', 'charges', data=request.to_dict())

        payment = TapPaymentResponse.from_response(response)

        logger.info(f"Tap payment created: {payment.id} - Status: {payment.status.value}")

        return payment

    def retrieve_payment(self, charge_id: str) -> TapPaymentResponse:
        """استرجاع تفاصيل عملية دفع"""
        response = self._make_request('GET', f'charges/{charge_id}')
        return TapPaymentResponse.from_response(response)

    def capture_payment(self, charge_id: str, amount: Optional[Decimal] = None) -> Dict[str, Any]:
        """التقاط دفعة مُفوَّضة"""
        data = {}
        if amount:
            data['amount'] = float(amount)

        return self._make_request('POST', f'charges/{charge_id}/capture', data=data)

    def refund_payment(
        self,
        charge_id: str,
        amount: Decimal,
        reason: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """استرجاع مبلغ"""
        data = {
            'charge_id': charge_id,
            'amount': float(amount),
            'reason': reason,
            'metadata': metadata or {},
        }

        logger.info(f"Creating refund for charge: {charge_id}, amount: {amount}")
        return self._make_request('POST', 'refunds', data=data)

    # =====================================
    # التحويلات والتسوية
    # =====================================

    def list_transfers(
        self,
        destination_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[TapTransferStatus] = None,
        limit: int = 25
    ) -> Dict[str, Any]:
        """
        قائمة التحويلات - للتسوية
        """
        params = {'limit': limit}

        if destination_id:
            params['destination'] = destination_id
        if start_date:
            params['created[gte]'] = int(start_date.timestamp())
        if end_date:
            params['created[lte]'] = int(end_date.timestamp())
        if status:
            params['status'] = status.value

        return self._make_request('GET', 'transfers', params=params)

    def get_balance(self, account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        استرجاع الرصيد
        """
        endpoint = 'balance'
        if account_id:
            endpoint = f'connect/accounts/{account_id}/balance'

        return self._make_request('GET', endpoint)

    def get_settlement_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        تقرير التسوية لفترة محددة
        يُستخدم للمقارنة مع سجلاتنا
        """
        params = {
            'created[gte]': int(start_date.timestamp()),
            'created[lte]': int(end_date.timestamp()),
        }

        charges = self._make_request('GET', 'charges', params={
            **params, 'limit': 100
        })

        transfers = self._make_request('GET', 'transfers', params={
            **params, 'limit': 100
        })

        return {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            },
            'charges': charges.get('data', []),
            'transfers': transfers.get('data', []),
            'totals': {
                'charges_count': charges.get('count', 0),
                'transfers_count': transfers.get('count', 0),
            }
        }

    # =====================================
    # Webhooks
    # =====================================

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str
    ) -> bool:
        """
        التحقق من توقيع Webhook

        يضمن أن الطلب قادم فعلاً من Tap
        """
        if not self.webhook_secret:
            logger.warning("Tap webhook secret not configured")
            return False

        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)

    def parse_webhook_event(
        self,
        payload: bytes,
        signature: str
    ) -> Optional[Dict[str, Any]]:
        """
        معالجة حدث Webhook
        """
        if not self.verify_webhook_signature(payload, signature):
            logger.warning("Invalid Tap webhook signature")
            return None

        try:
            event = json.loads(payload)
            logger.info(f"Received Tap webhook: {event.get('type')}")
            return event
        except json.JSONDecodeError:
            logger.error("Invalid Tap webhook payload")
            return None

    # =====================================
    # أدوات مساعدة
    # =====================================

    def calculate_platform_commission(
        self,
        amount: Decimal,
        vendor_amount: Decimal,
        driver_amount: Decimal = Decimal('0')
    ) -> Decimal:
        """
        حساب عمولة المنصة
        المتبقي بعد توزيع المبالغ على البائعين
        """
        total_destinations = vendor_amount + driver_amount
        return amount - total_destinations

    def prepare_payment_destinations(
        self,
        vendor_tap_id: str,
        vendor_amount: Decimal,
        driver_tap_id: Optional[str] = None,
        driver_amount: Decimal = Decimal('0')
    ) -> List[TapDestination]:
        """
        تحضير وجهات التقسيم
        """
        destinations = [
            TapDestination(
                id=vendor_tap_id,
                amount=vendor_amount,
                description='حصة التاجر'
            )
        ]

        if driver_tap_id and driver_amount > 0:
            destinations.append(
                TapDestination(
                    id=driver_tap_id,
                    amount=driver_amount,
                    description='حصة السائق'
                )
            )

        return destinations


# Singleton instance
tap_client = TapConnectClient()
