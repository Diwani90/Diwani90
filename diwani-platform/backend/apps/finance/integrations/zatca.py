"""
===================================
منصة ديواني - ZATCA E-Invoice Integration
تكامل الفوترة الإلكترونية مع هيئة الزكاة والضريبة والجمارك
===================================

متطلبات ZATCA للفوترة الإلكترونية (المرحلة الثانية):
- التوقيع الرقمي للفواتير
- توليد QR Code محلياً
- حساب Invoice Hash
- الربط المباشر مع منصة ZATCA

المواصفات: ZATCA E-invoicing Standard v2.0.0
"""

import base64
import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from io import BytesIO
from typing import Any, Dict, List, Optional

import qrcode
import requests
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from cryptography.x509.oid import NameOID
from django.conf import settings
from django.core.cache import cache
from lxml import etree

logger = logging.getLogger(__name__)


class ZATCAEnvironment(Enum):
    """بيئات ZATCA"""
    SANDBOX = 'sandbox'
    SIMULATION = 'simulation'
    PRODUCTION = 'production'


class InvoiceType(Enum):
    """أنواع الفواتير"""
    STANDARD = '388'  # فاتورة ضريبية قياسية
    SIMPLIFIED = '381'  # فاتورة ضريبية مبسطة
    DEBIT_NOTE = '383'  # إشعار مدين
    CREDIT_NOTE = '381'  # إشعار دائن


class InvoiceSubtype(Enum):
    """أنواع فرعية للفواتير"""
    STANDARD_INVOICE = '0100000'  # فاتورة ضريبية
    SIMPLIFIED_INVOICE = '0200000'  # فاتورة ضريبية مبسطة
    STANDARD_DEBIT = '0100001'
    STANDARD_CREDIT = '0100010'
    SIMPLIFIED_DEBIT = '0200001'
    SIMPLIFIED_CREDIT = '0200010'


@dataclass
class ZATCAInvoiceItem:
    """عنصر في الفاتورة"""
    name: str
    quantity: Decimal
    unit_price: Decimal
    discount: Decimal = Decimal('0')
    tax_rate: Decimal = Decimal('15')  # VAT 15%
    unit_code: str = 'PCE'  # قطعة

    @property
    def line_extension_amount(self) -> Decimal:
        """المبلغ قبل الضريبة"""
        return (self.quantity * self.unit_price) - self.discount

    @property
    def tax_amount(self) -> Decimal:
        """مبلغ الضريبة"""
        return self.line_extension_amount * (self.tax_rate / 100)

    @property
    def total_amount(self) -> Decimal:
        """المبلغ الإجمالي"""
        return self.line_extension_amount + self.tax_amount


@dataclass
class ZATCASeller:
    """بيانات البائع"""
    name: str
    vat_number: str
    cr_number: str  # رقم السجل التجاري
    street: str
    building: str
    city: str
    district: str
    postal_code: str
    country: str = 'SA'


@dataclass
class ZATCABuyer:
    """بيانات المشتري"""
    name: str
    vat_number: Optional[str] = None
    address: Optional[str] = None


@dataclass
class ZATCAInvoice:
    """بيانات الفاتورة الكاملة"""
    uuid: str
    invoice_number: str
    invoice_date: datetime
    invoice_type: InvoiceType
    invoice_subtype: InvoiceSubtype
    seller: ZATCASeller
    buyer: ZATCABuyer
    items: List[ZATCAInvoiceItem]
    previous_invoice_hash: str = ''
    currency: str = 'SAR'
    payment_method: str = '10'  # 10 = نقدي، 30 = ائتمان، 48 = بطاقة
    notes: Optional[str] = None

    @property
    def subtotal(self) -> Decimal:
        """المجموع قبل الضريبة"""
        return sum(item.line_extension_amount for item in self.items)

    @property
    def total_tax(self) -> Decimal:
        """إجمالي الضريبة"""
        return sum(item.tax_amount for item in self.items)

    @property
    def total_discount(self) -> Decimal:
        """إجمالي الخصم"""
        return sum(item.discount for item in self.items)

    @property
    def total_amount(self) -> Decimal:
        """الإجمالي مع الضريبة"""
        return self.subtotal + self.total_tax


class ZATCAXMLBuilder:
    """
    منشئ XML للفاتورة الإلكترونية

    يتبع مواصفات UBL 2.1 و ZATCA
    """

    NAMESPACES = {
        None: 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
        'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
        'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
        'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
        'sig': 'urn:oasis:names:specification:ubl:schema:xsd:CommonSignatureComponents-2',
        'sac': 'urn:oasis:names:specification:ubl:schema:xsd:SignatureAggregateComponents-2',
        'sbc': 'urn:oasis:names:specification:ubl:schema:xsd:SignatureBasicComponents-2',
    }

    def __init__(self, invoice: ZATCAInvoice):
        self.invoice = invoice

    def build(self) -> str:
        """بناء XML الفاتورة"""
        nsmap = {k: v for k, v in self.NAMESPACES.items() if k is not None}
        nsmap[None] = self.NAMESPACES[None]

        root = etree.Element(
            'Invoice',
            nsmap=nsmap
        )

        # معرفات الفاتورة
        self._add_invoice_identifiers(root)

        # بيانات البائع
        self._add_seller_party(root)

        # بيانات المشتري
        self._add_buyer_party(root)

        # طريقة الدفع
        self._add_payment_means(root)

        # ملخص الضريبة
        self._add_tax_total(root)

        # المبلغ الإجمالي
        self._add_legal_monetary_total(root)

        # عناصر الفاتورة
        for idx, item in enumerate(self.invoice.items, 1):
            self._add_invoice_line(root, item, idx)

        return etree.tostring(
            root,
            encoding='unicode',
            pretty_print=True,
            xml_declaration=True
        )

    def _add_invoice_identifiers(self, root):
        """إضافة معرفات الفاتورة"""
        cbc = '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}'

        # UBL Version
        etree.SubElement(root, f'{cbc}UBLVersionID').text = '2.1'

        # Profile ID
        etree.SubElement(root, f'{cbc}ProfileID').text = 'reporting:1.0'

        # UUID
        etree.SubElement(root, f'{cbc}UUID').text = self.invoice.uuid

        # رقم الفاتورة
        etree.SubElement(root, f'{cbc}ID').text = self.invoice.invoice_number

        # تاريخ الإصدار
        etree.SubElement(root, f'{cbc}IssueDate').text = self.invoice.invoice_date.strftime('%Y-%m-%d')
        etree.SubElement(root, f'{cbc}IssueTime').text = self.invoice.invoice_date.strftime('%H:%M:%S')

        # نوع الفاتورة
        invoice_type = etree.SubElement(root, f'{cbc}InvoiceTypeCode')
        invoice_type.text = self.invoice.invoice_type.value
        invoice_type.set('name', self.invoice.invoice_subtype.value)

        # العملة
        etree.SubElement(root, f'{cbc}DocumentCurrencyCode').text = self.invoice.currency

        # الضريبة
        etree.SubElement(root, f'{cbc}TaxCurrencyCode').text = self.invoice.currency

        # الملاحظات
        if self.invoice.notes:
            etree.SubElement(root, f'{cbc}Note').text = self.invoice.notes

    def _add_seller_party(self, root):
        """إضافة بيانات البائع"""
        cac = '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}'
        cbc = '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}'

        supplier = etree.SubElement(root, f'{cac}AccountingSupplierParty')
        party = etree.SubElement(supplier, f'{cac}Party')

        # معرف الطرف
        party_id = etree.SubElement(party, f'{cac}PartyIdentification')
        id_elem = etree.SubElement(party_id, f'{cbc}ID')
        id_elem.text = self.invoice.seller.cr_number
        id_elem.set('schemeID', 'CRN')

        # العنوان
        address = etree.SubElement(party, f'{cac}PostalAddress')
        etree.SubElement(address, f'{cbc}StreetName').text = self.invoice.seller.street
        etree.SubElement(address, f'{cbc}BuildingNumber').text = self.invoice.seller.building
        etree.SubElement(address, f'{cbc}CityName').text = self.invoice.seller.city
        etree.SubElement(address, f'{cbc}PostalZone').text = self.invoice.seller.postal_code
        etree.SubElement(address, f'{cbc}District').text = self.invoice.seller.district

        country = etree.SubElement(address, f'{cac}Country')
        etree.SubElement(country, f'{cbc}IdentificationCode').text = self.invoice.seller.country

        # الرقم الضريبي
        tax_scheme = etree.SubElement(party, f'{cac}PartyTaxScheme')
        etree.SubElement(tax_scheme, f'{cbc}CompanyID').text = self.invoice.seller.vat_number
        scheme = etree.SubElement(tax_scheme, f'{cac}TaxScheme')
        etree.SubElement(scheme, f'{cbc}ID').text = 'VAT'

        # اسم الشركة
        legal = etree.SubElement(party, f'{cac}PartyLegalEntity')
        etree.SubElement(legal, f'{cbc}RegistrationName').text = self.invoice.seller.name

    def _add_buyer_party(self, root):
        """إضافة بيانات المشتري"""
        cac = '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}'
        cbc = '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}'

        customer = etree.SubElement(root, f'{cac}AccountingCustomerParty')
        party = etree.SubElement(customer, f'{cac}Party')

        # الاسم
        legal = etree.SubElement(party, f'{cac}PartyLegalEntity')
        etree.SubElement(legal, f'{cbc}RegistrationName').text = self.invoice.buyer.name

        # الرقم الضريبي (إذا وُجد)
        if self.invoice.buyer.vat_number:
            tax_scheme = etree.SubElement(party, f'{cac}PartyTaxScheme')
            etree.SubElement(tax_scheme, f'{cbc}CompanyID').text = self.invoice.buyer.vat_number
            scheme = etree.SubElement(tax_scheme, f'{cac}TaxScheme')
            etree.SubElement(scheme, f'{cbc}ID').text = 'VAT'

    def _add_payment_means(self, root):
        """طريقة الدفع"""
        cac = '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}'
        cbc = '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}'

        payment = etree.SubElement(root, f'{cac}PaymentMeans')
        etree.SubElement(payment, f'{cbc}PaymentMeansCode').text = self.invoice.payment_method

    def _add_tax_total(self, root):
        """ملخص الضريبة"""
        cac = '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}'
        cbc = '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}'

        tax_total = etree.SubElement(root, f'{cac}TaxTotal')
        tax_amount = etree.SubElement(tax_total, f'{cbc}TaxAmount')
        tax_amount.text = f'{self.invoice.total_tax:.2f}'
        tax_amount.set('currencyID', self.invoice.currency)

        # تفاصيل الضريبة
        subtotal = etree.SubElement(tax_total, f'{cac}TaxSubtotal')

        taxable = etree.SubElement(subtotal, f'{cbc}TaxableAmount')
        taxable.text = f'{self.invoice.subtotal:.2f}'
        taxable.set('currencyID', self.invoice.currency)

        tax_amt = etree.SubElement(subtotal, f'{cbc}TaxAmount')
        tax_amt.text = f'{self.invoice.total_tax:.2f}'
        tax_amt.set('currencyID', self.invoice.currency)

        category = etree.SubElement(subtotal, f'{cac}TaxCategory')
        etree.SubElement(category, f'{cbc}ID').text = 'S'  # Standard
        etree.SubElement(category, f'{cbc}Percent').text = '15'

        scheme = etree.SubElement(category, f'{cac}TaxScheme')
        etree.SubElement(scheme, f'{cbc}ID').text = 'VAT'

    def _add_legal_monetary_total(self, root):
        """المبالغ الإجمالية"""
        cac = '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}'
        cbc = '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}'

        monetary = etree.SubElement(root, f'{cac}LegalMonetaryTotal')

        # المجموع الفرعي
        line_ext = etree.SubElement(monetary, f'{cbc}LineExtensionAmount')
        line_ext.text = f'{self.invoice.subtotal:.2f}'
        line_ext.set('currencyID', self.invoice.currency)

        # المجموع قبل الضريبة
        tax_excl = etree.SubElement(monetary, f'{cbc}TaxExclusiveAmount')
        tax_excl.text = f'{self.invoice.subtotal:.2f}'
        tax_excl.set('currencyID', self.invoice.currency)

        # المجموع مع الضريبة
        tax_incl = etree.SubElement(monetary, f'{cbc}TaxInclusiveAmount')
        tax_incl.text = f'{self.invoice.total_amount:.2f}'
        tax_incl.set('currencyID', self.invoice.currency)

        # المبلغ المستحق
        payable = etree.SubElement(monetary, f'{cbc}PayableAmount')
        payable.text = f'{self.invoice.total_amount:.2f}'
        payable.set('currencyID', self.invoice.currency)

    def _add_invoice_line(self, root, item: ZATCAInvoiceItem, line_id: int):
        """إضافة سطر في الفاتورة"""
        cac = '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}'
        cbc = '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}'

        line = etree.SubElement(root, f'{cac}InvoiceLine')

        etree.SubElement(line, f'{cbc}ID').text = str(line_id)

        # الكمية
        qty = etree.SubElement(line, f'{cbc}InvoicedQuantity')
        qty.text = str(item.quantity)
        qty.set('unitCode', item.unit_code)

        # المبلغ
        amount = etree.SubElement(line, f'{cbc}LineExtensionAmount')
        amount.text = f'{item.line_extension_amount:.2f}'
        amount.set('currencyID', self.invoice.currency)

        # الضريبة
        tax_total = etree.SubElement(line, f'{cac}TaxTotal')
        tax_amt = etree.SubElement(tax_total, f'{cbc}TaxAmount')
        tax_amt.text = f'{item.tax_amount:.2f}'
        tax_amt.set('currencyID', self.invoice.currency)

        # تفاصيل المنتج
        item_elem = etree.SubElement(line, f'{cac}Item')
        etree.SubElement(item_elem, f'{cbc}Name').text = item.name

        # تصنيف الضريبة
        tax_cat = etree.SubElement(item_elem, f'{cac}ClassifiedTaxCategory')
        etree.SubElement(tax_cat, f'{cbc}ID').text = 'S'
        etree.SubElement(tax_cat, f'{cbc}Percent').text = str(item.tax_rate)

        scheme = etree.SubElement(tax_cat, f'{cac}TaxScheme')
        etree.SubElement(scheme, f'{cbc}ID').text = 'VAT'

        # السعر
        price = etree.SubElement(line, f'{cac}Price')
        price_amt = etree.SubElement(price, f'{cbc}PriceAmount')
        price_amt.text = f'{item.unit_price:.2f}'
        price_amt.set('currencyID', self.invoice.currency)


class ZATCAQRGenerator:
    """
    منشئ QR Code لـ ZATCA

    يتبع المواصفات السعودية لـ TLV encoding
    """

    # TLV Tags
    SELLER_NAME = 1
    VAT_NUMBER = 2
    TIMESTAMP = 3
    TOTAL_WITH_VAT = 4
    VAT_AMOUNT = 5
    INVOICE_HASH = 6
    SIGNATURE = 7
    PUBLIC_KEY = 8
    SIGNATURE_ALGORITHM = 9

    @staticmethod
    def _encode_tlv(tag: int, value: str) -> bytes:
        """تشفير TLV"""
        value_bytes = value.encode('utf-8')
        return bytes([tag, len(value_bytes)]) + value_bytes

    @classmethod
    def generate(
        cls,
        seller_name: str,
        vat_number: str,
        timestamp: datetime,
        total_with_vat: Decimal,
        vat_amount: Decimal,
        invoice_hash: Optional[str] = None,
        signature: Optional[bytes] = None,
        public_key: Optional[bytes] = None
    ) -> str:
        """
        توليد QR Code

        Args:
            seller_name: اسم البائع
            vat_number: الرقم الضريبي
            timestamp: وقت الإصدار
            total_with_vat: الإجمالي مع الضريبة
            vat_amount: مبلغ الضريبة
            invoice_hash: هاش الفاتورة (للمرحلة 2)
            signature: التوقيع الرقمي (للمرحلة 2)
            public_key: المفتاح العام (للمرحلة 2)

        Returns:
            Base64 encoded QR data
        """
        # البيانات الأساسية (المرحلة 1)
        data = b''
        data += cls._encode_tlv(cls.SELLER_NAME, seller_name)
        data += cls._encode_tlv(cls.VAT_NUMBER, vat_number)
        data += cls._encode_tlv(cls.TIMESTAMP, timestamp.isoformat())
        data += cls._encode_tlv(cls.TOTAL_WITH_VAT, f'{total_with_vat:.2f}')
        data += cls._encode_tlv(cls.VAT_AMOUNT, f'{vat_amount:.2f}')

        # البيانات المتقدمة (المرحلة 2)
        if invoice_hash:
            data += cls._encode_tlv(cls.INVOICE_HASH, invoice_hash)
        if signature:
            data += bytes([cls.SIGNATURE, len(signature)]) + signature
        if public_key:
            data += bytes([cls.PUBLIC_KEY, len(public_key)]) + public_key

        return base64.b64encode(data).decode('ascii')

    @classmethod
    def generate_qr_image(
        cls,
        qr_data: str,
        box_size: int = 10,
        border: int = 4
    ) -> bytes:
        """توليد صورة QR Code"""
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=box_size,
            border=border,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()


class ZATCASigner:
    """
    موقّع الفواتير الرقمي

    يستخدم ECDSA مع منحنى secp256k1
    """

    def __init__(
        self,
        private_key_path: Optional[str] = None,
        certificate_path: Optional[str] = None
    ):
        self.private_key_path = private_key_path or getattr(
            settings, 'ZATCA_PRIVATE_KEY_PATH', ''
        )
        self.certificate_path = certificate_path or getattr(
            settings, 'ZATCA_CERTIFICATE_PATH', ''
        )
        self._private_key = None
        self._certificate = None

    @property
    def private_key(self):
        """تحميل المفتاح الخاص"""
        if self._private_key is None and self.private_key_path:
            with open(self.private_key_path, 'rb') as f:
                self._private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None,
                    backend=default_backend()
                )
        return self._private_key

    @property
    def certificate(self):
        """تحميل الشهادة"""
        if self._certificate is None and self.certificate_path:
            with open(self.certificate_path, 'rb') as f:
                self._certificate = x509.load_pem_x509_certificate(
                    f.read(),
                    backend=default_backend()
                )
        return self._certificate

    def sign(self, data: bytes) -> bytes:
        """توقيع البيانات"""
        if not self.private_key:
            raise ValueError("Private key not loaded")

        signature = self.private_key.sign(
            data,
            ec.ECDSA(hashes.SHA256())
        )
        return signature

    def get_public_key_bytes(self) -> bytes:
        """الحصول على المفتاح العام"""
        if not self.certificate:
            raise ValueError("Certificate not loaded")

        public_key = self.certificate.public_key()
        return public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def get_certificate_hash(self) -> str:
        """هاش الشهادة"""
        if not self.certificate:
            raise ValueError("Certificate not loaded")

        cert_bytes = self.certificate.public_bytes(
            encoding=serialization.Encoding.DER
        )
        return hashlib.sha256(cert_bytes).hexdigest()


class ZATCAService:
    """
    خدمة ZATCA الرئيسية

    تدعم:
    - Compliance CSID (للاختبار)
    - Production CSID
    - Reporting
    - Clearance
    """

    ENVIRONMENTS = {
        ZATCAEnvironment.SANDBOX: 'https://gw-fatoora.zatca.gov.sa/e-invoicing/developer-portal',
        ZATCAEnvironment.SIMULATION: 'https://gw-fatoora.zatca.gov.sa/e-invoicing/simulation',
        ZATCAEnvironment.PRODUCTION: 'https://gw-fatoora.zatca.gov.sa/e-invoicing/core',
    }

    def __init__(
        self,
        environment: Optional[ZATCAEnvironment] = None,
        certificate_path: Optional[str] = None,
        private_key_path: Optional[str] = None
    ):
        self.environment = environment or ZATCAEnvironment(
            getattr(settings, 'ZATCA_ENVIRONMENT', 'sandbox')
        )
        self.base_url = self.ENVIRONMENTS[self.environment]
        self.signer = ZATCASigner(private_key_path, certificate_path)
        self._session = None

    @property
    def session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                'Content-Type': 'application/json',
                'Accept-Language': 'ar',
            })
        return self._session

    def compute_invoice_hash(self, xml_content: str) -> str:
        """حساب هاش الفاتورة"""
        # تنظيف XML (إزالة التوقيع والـ QR إن وُجدا)
        clean_xml = self._prepare_xml_for_hash(xml_content)

        # SHA-256 hash
        hash_bytes = hashlib.sha256(clean_xml.encode('utf-8')).digest()
        return base64.b64encode(hash_bytes).decode('ascii')

    def _prepare_xml_for_hash(self, xml_content: str) -> str:
        """تحضير XML للـ Hash"""
        # Remove UBLExtensions, Signature, and QR elements
        tree = etree.fromstring(xml_content.encode())

        # إزالة عناصر التوقيع
        for elem in tree.xpath('//*[local-name()="UBLExtensions"]'):
            elem.getparent().remove(elem)

        for elem in tree.xpath('//*[local-name()="QRCode"]'):
            elem.getparent().remove(elem)

        return etree.tostring(tree, encoding='unicode')

    def create_invoice(self, invoice: ZATCAInvoice) -> Dict[str, Any]:
        """
        إنشاء فاتورة إلكترونية كاملة

        Returns:
            Dict with xml, qr_code, hash, signature
        """
        # بناء XML
        builder = ZATCAXMLBuilder(invoice)
        xml_content = builder.build()

        # حساب Hash
        invoice_hash = self.compute_invoice_hash(xml_content)

        # التوقيع (إذا كانت المفاتيح متوفرة)
        signature = None
        public_key = None
        try:
            signature = self.signer.sign(invoice_hash.encode())
            public_key = self.signer.get_public_key_bytes()
        except ValueError:
            logger.warning("ZATCA keys not configured, skipping signature")

        # توليد QR
        qr_data = ZATCAQRGenerator.generate(
            seller_name=invoice.seller.name,
            vat_number=invoice.seller.vat_number,
            timestamp=invoice.invoice_date,
            total_with_vat=invoice.total_amount,
            vat_amount=invoice.total_tax,
            invoice_hash=invoice_hash,
            signature=signature,
            public_key=public_key
        )

        qr_image = ZATCAQRGenerator.generate_qr_image(qr_data)

        return {
            'xml': xml_content,
            'hash': invoice_hash,
            'qr_data': qr_data,
            'qr_image': base64.b64encode(qr_image).decode('ascii'),
            'signature': base64.b64encode(signature).decode('ascii') if signature else None,
            'uuid': invoice.uuid,
            'invoice_number': invoice.invoice_number,
        }

    def report_invoice(
        self,
        invoice_hash: str,
        uuid: str,
        xml_content: str
    ) -> Dict[str, Any]:
        """
        إبلاغ ZATCA بالفاتورة (Reporting)

        للفواتير المبسطة
        """
        endpoint = f'{self.base_url}/invoices/reporting/single'

        payload = {
            'invoiceHash': invoice_hash,
            'uuid': uuid,
            'invoice': base64.b64encode(xml_content.encode()).decode(),
        }

        try:
            response = self.session.post(
                endpoint,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"ZATCA reporting error: {e}")
            return {
                'success': False,
                'error': str(e),
            }

    def clearance_invoice(
        self,
        invoice_hash: str,
        uuid: str,
        xml_content: str
    ) -> Dict[str, Any]:
        """
        اعتماد الفاتورة من ZATCA (Clearance)

        للفواتير القياسية B2B
        """
        endpoint = f'{self.base_url}/invoices/clearance/single'

        payload = {
            'invoiceHash': invoice_hash,
            'uuid': uuid,
            'invoice': base64.b64encode(xml_content.encode()).decode(),
        }

        try:
            response = self.session.post(
                endpoint,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"ZATCA clearance error: {e}")
            return {
                'success': False,
                'error': str(e),
            }


# ===================================
# Helper Functions
# ===================================
def create_zatca_invoice_from_order(order) -> ZATCAInvoice:
    """
    تحويل Order إلى ZATCAInvoice

    Args:
        order: Order instance from orders app

    Returns:
        ZATCAInvoice ready for processing
    """
    from apps.stores.models import Store

    store = order.store

    # بيانات البائع من المتجر
    seller = ZATCASeller(
        name=store.vendor.company_name,
        vat_number=store.vendor.vat_number or '',
        cr_number=store.vendor.commercial_register or '',
        street=store.address or '',
        building='',
        city=store.city or 'الرياض',
        district=store.district or '',
        postal_code=store.postal_code or '',
    )

    # بيانات المشتري
    buyer = ZATCABuyer(
        name=order.customer.get_full_name() or order.customer.phone,
        vat_number=None,  # العملاء العاديين ليس لديهم VAT
    )

    # عناصر الفاتورة
    items = []
    for item in order.items.all():
        items.append(ZATCAInvoiceItem(
            name=item.product.name,
            quantity=Decimal(str(item.quantity)),
            unit_price=item.unit_price,
            discount=item.discount or Decimal('0'),
            tax_rate=Decimal('15'),
        ))

    # نوع الفاتورة
    invoice_type = InvoiceType.SIMPLIFIED  # B2C
    invoice_subtype = InvoiceSubtype.SIMPLIFIED_INVOICE

    return ZATCAInvoice(
        uuid=str(uuid.uuid4()),
        invoice_number=order.order_number,
        invoice_date=order.created_at,
        invoice_type=invoice_type,
        invoice_subtype=invoice_subtype,
        seller=seller,
        buyer=buyer,
        items=items,
        payment_method='48' if order.payment_method == 'card' else '10',
    )


# Singleton service
zatca_service = ZATCAService()
