"""
خدمات النظام المالي
===================

محرك التسوية وحاسبات التسعير والعمولات
Reconciliation Engine, Pricing & Commission Calculators
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

from django.conf import settings
from django.db import transaction
from django.db.models import Sum, Q, F
from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)


# ===========================================
# استراتيجيات التسعير - Pricing Strategies
# ===========================================

class PricingStrategy(ABC):
    """
    استراتيجية التسعير الأساسية
    Strategy Pattern للتعامل مع أنواع التسعير المختلفة
    """

    @abstractmethod
    def calculate(self, base_price: Decimal, quantity: Decimal,
                  context: Dict[str, Any]) -> Decimal:
        """حساب السعر النهائي"""
        pass

    @abstractmethod
    def get_breakdown(self, base_price: Decimal, quantity: Decimal,
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """الحصول على تفاصيل الحساب"""
        pass


class FixedPricingStrategy(PricingStrategy):
    """سعر ثابت للوحدة"""

    def calculate(self, base_price: Decimal, quantity: Decimal,
                  context: Dict[str, Any]) -> Decimal:
        return (base_price * quantity).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def get_breakdown(self, base_price: Decimal, quantity: Decimal,
                      context: Dict[str, Any]) -> Dict[str, Any]:
        total = self.calculate(base_price, quantity, context)
        return {
            'type': 'fixed',
            'base_price': float(base_price),
            'quantity': float(quantity),
            'subtotal': float(total),
            'total': float(total),
        }


class HourlyPricingStrategy(PricingStrategy):
    """تسعير بالساعة - للمعدات والخدمات"""

    def __init__(self, minimum_hours: int = 1, rounding_interval: int = 30):
        self.minimum_hours = minimum_hours
        self.rounding_interval = rounding_interval  # بالدقائق

    def _round_hours(self, hours: Decimal) -> Decimal:
        """تقريب الساعات لأقرب فترة"""
        minutes = hours * 60
        rounded_minutes = (minutes / self.rounding_interval).quantize(
            Decimal('1'), rounding=ROUND_HALF_UP
        ) * self.rounding_interval
        return max(
            Decimal(self.minimum_hours),
            (rounded_minutes / 60).quantize(Decimal('0.5'), rounding=ROUND_HALF_UP)
        )

    def calculate(self, base_price: Decimal, quantity: Decimal,
                  context: Dict[str, Any]) -> Decimal:
        hours = context.get('hours', quantity)
        billable_hours = self._round_hours(Decimal(str(hours)))

        # معامل الذروة (اختياري)
        peak_multiplier = Decimal(str(context.get('peak_multiplier', 1.0)))

        total = base_price * billable_hours * peak_multiplier
        return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def get_breakdown(self, base_price: Decimal, quantity: Decimal,
                      context: Dict[str, Any]) -> Dict[str, Any]:
        hours = context.get('hours', quantity)
        billable_hours = self._round_hours(Decimal(str(hours)))
        peak_multiplier = Decimal(str(context.get('peak_multiplier', 1.0)))

        subtotal = base_price * billable_hours
        peak_charge = subtotal * (peak_multiplier - 1) if peak_multiplier > 1 else Decimal('0')
        total = subtotal + peak_charge

        return {
            'type': 'hourly',
            'hourly_rate': float(base_price),
            'actual_hours': float(hours),
            'billable_hours': float(billable_hours),
            'minimum_hours': self.minimum_hours,
            'peak_multiplier': float(peak_multiplier),
            'subtotal': float(subtotal),
            'peak_charge': float(peak_charge),
            'total': float(total.quantize(Decimal('0.01'))),
        }


class DailyPricingStrategy(PricingStrategy):
    """تسعير باليوم - للمعدات والإيجارات"""

    def __init__(self, minimum_days: int = 1, weekly_discount: Decimal = Decimal('0.10'),
                 monthly_discount: Decimal = Decimal('0.20')):
        self.minimum_days = minimum_days
        self.weekly_discount = weekly_discount
        self.monthly_discount = monthly_discount

    def _calculate_discount(self, days: int) -> Decimal:
        """حساب الخصم بناءً على مدة الإيجار"""
        if days >= 30:
            return self.monthly_discount
        elif days >= 7:
            return self.weekly_discount
        return Decimal('0')

    def calculate(self, base_price: Decimal, quantity: Decimal,
                  context: Dict[str, Any]) -> Decimal:
        days = max(self.minimum_days, int(context.get('days', quantity)))

        subtotal = base_price * days
        discount = self._calculate_discount(days)
        discount_amount = subtotal * discount

        total = subtotal - discount_amount
        return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def get_breakdown(self, base_price: Decimal, quantity: Decimal,
                      context: Dict[str, Any]) -> Dict[str, Any]:
        days = max(self.minimum_days, int(context.get('days', quantity)))

        subtotal = base_price * days
        discount = self._calculate_discount(days)
        discount_amount = subtotal * discount
        total = subtotal - discount_amount

        return {
            'type': 'daily',
            'daily_rate': float(base_price),
            'days': days,
            'minimum_days': self.minimum_days,
            'subtotal': float(subtotal),
            'discount_percentage': float(discount * 100),
            'discount_amount': float(discount_amount),
            'total': float(total.quantize(Decimal('0.01'))),
        }


class DistancePricingStrategy(PricingStrategy):
    """تسعير بالمسافة - للتوصيل"""

    def __init__(self, base_fee: Decimal = Decimal('0'),
                 free_km: int = 0,
                 max_distance: Optional[int] = None):
        self.base_fee = base_fee
        self.free_km = free_km
        self.max_distance = max_distance

    def calculate(self, base_price: Decimal, quantity: Decimal,
                  context: Dict[str, Any]) -> Decimal:
        distance_km = Decimal(str(context.get('distance_km', quantity)))

        if self.max_distance and distance_km > self.max_distance:
            raise ValueError(f"المسافة تتجاوز الحد الأقصى ({self.max_distance} كم)")

        # المسافة المحسوبة بعد خصم الكيلومترات المجانية
        billable_km = max(Decimal('0'), distance_km - self.free_km)

        total = self.base_fee + (base_price * billable_km)
        return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def get_breakdown(self, base_price: Decimal, quantity: Decimal,
                      context: Dict[str, Any]) -> Dict[str, Any]:
        distance_km = Decimal(str(context.get('distance_km', quantity)))
        billable_km = max(Decimal('0'), distance_km - self.free_km)
        distance_charge = base_price * billable_km
        total = self.base_fee + distance_charge

        return {
            'type': 'distance',
            'rate_per_km': float(base_price),
            'total_distance_km': float(distance_km),
            'free_km': self.free_km,
            'billable_km': float(billable_km),
            'base_fee': float(self.base_fee),
            'distance_charge': float(distance_charge),
            'total': float(total.quantize(Decimal('0.01'))),
        }


class WeightPricingStrategy(PricingStrategy):
    """تسعير بالوزن - للمواد السائبة والخرسانة"""

    def __init__(self, minimum_weight: Decimal = Decimal('0'),
                 weight_unit: str = 'ton'):
        self.minimum_weight = minimum_weight
        self.weight_unit = weight_unit

    def calculate(self, base_price: Decimal, quantity: Decimal,
                  context: Dict[str, Any]) -> Decimal:
        weight = Decimal(str(context.get('weight', quantity)))
        billable_weight = max(self.minimum_weight, weight)

        total = base_price * billable_weight
        return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def get_breakdown(self, base_price: Decimal, quantity: Decimal,
                      context: Dict[str, Any]) -> Dict[str, Any]:
        weight = Decimal(str(context.get('weight', quantity)))
        billable_weight = max(self.minimum_weight, weight)
        total = base_price * billable_weight

        return {
            'type': 'weight',
            'price_per_unit': float(base_price),
            'weight_unit': self.weight_unit,
            'actual_weight': float(weight),
            'minimum_weight': float(self.minimum_weight),
            'billable_weight': float(billable_weight),
            'total': float(total.quantize(Decimal('0.01'))),
        }


class TieredPricingStrategy(PricingStrategy):
    """تسعير متدرج - خصومات على الكميات الكبيرة"""

    def __init__(self, tiers: List[Tuple[int, Decimal]]):
        """
        tiers: قائمة من (الحد الأدنى, سعر الوحدة)
        مثال: [(1, 100), (10, 90), (50, 80), (100, 70)]
        """
        self.tiers = sorted(tiers, key=lambda x: x[0], reverse=True)

    def _get_tier_price(self, quantity: int) -> Decimal:
        """الحصول على سعر الوحدة للكمية المحددة"""
        for min_qty, price in self.tiers:
            if quantity >= min_qty:
                return price
        return self.tiers[-1][1]  # السعر الأساسي

    def calculate(self, base_price: Decimal, quantity: Decimal,
                  context: Dict[str, Any]) -> Decimal:
        qty = int(quantity)
        unit_price = self._get_tier_price(qty)

        total = unit_price * qty
        return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def get_breakdown(self, base_price: Decimal, quantity: Decimal,
                      context: Dict[str, Any]) -> Dict[str, Any]:
        qty = int(quantity)
        unit_price = self._get_tier_price(qty)
        original_total = base_price * qty
        final_total = unit_price * qty
        savings = original_total - final_total

        return {
            'type': 'tiered',
            'quantity': qty,
            'original_price': float(base_price),
            'tier_price': float(unit_price),
            'discount_percentage': float((1 - unit_price / base_price) * 100) if base_price > 0 else 0,
            'original_total': float(original_total),
            'savings': float(savings),
            'total': float(final_total.quantize(Decimal('0.01'))),
            'tiers': [(t[0], float(t[1])) for t in self.tiers],
        }


class QuotePricingStrategy(PricingStrategy):
    """تسعير بالعرض - للطلبات الخاصة"""

    def calculate(self, base_price: Decimal, quantity: Decimal,
                  context: Dict[str, Any]) -> Decimal:
        quoted_price = context.get('quoted_price')
        if quoted_price is None:
            raise ValueError("يجب تحديد السعر المُعتمد للعرض")
        return Decimal(str(quoted_price)).quantize(Decimal('0.01'))

    def get_breakdown(self, base_price: Decimal, quantity: Decimal,
                      context: Dict[str, Any]) -> Dict[str, Any]:
        quoted_price = Decimal(str(context.get('quoted_price', 0)))
        quote_id = context.get('quote_id')
        quote_validity = context.get('quote_validity')

        return {
            'type': 'quote',
            'quote_id': quote_id,
            'quoted_price': float(quoted_price),
            'quote_validity': quote_validity,
            'total': float(quoted_price),
        }


class FreePricingStrategy(PricingStrategy):
    """مجاني - توصيل مجاني من التاجر"""

    def calculate(self, base_price: Decimal, quantity: Decimal,
                  context: Dict[str, Any]) -> Decimal:
        return Decimal('0.00')

    def get_breakdown(self, base_price: Decimal, quantity: Decimal,
                      context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'type': 'free',
            'reason': context.get('reason', 'توصيل مجاني'),
            'total': 0.0,
        }


# ===========================================
# مصنع استراتيجيات التسعير
# ===========================================

class PricingStrategyFactory:
    """مصنع لإنشاء استراتيجيات التسعير"""

    _strategies = {
        'fixed': FixedPricingStrategy,
        'per_unit': FixedPricingStrategy,
        'hourly': HourlyPricingStrategy,
        'per_hour': HourlyPricingStrategy,
        'daily': DailyPricingStrategy,
        'per_day': DailyPricingStrategy,
        'distance': DistancePricingStrategy,
        'per_km': DistancePricingStrategy,
        'weight': WeightPricingStrategy,
        'per_ton': WeightPricingStrategy,
        'per_m3': WeightPricingStrategy,
        'tiered': TieredPricingStrategy,
        'quote': QuotePricingStrategy,
        'free': FreePricingStrategy,
    }

    @classmethod
    def get_strategy(cls, pricing_type: str, **kwargs) -> PricingStrategy:
        """الحصول على استراتيجية التسعير المناسبة"""
        strategy_class = cls._strategies.get(pricing_type.lower())
        if not strategy_class:
            raise ValueError(f"نوع التسعير غير مدعوم: {pricing_type}")

        # معالجة المعاملات الخاصة بكل استراتيجية
        if pricing_type in ('tiered',):
            return strategy_class(tiers=kwargs.get('tiers', []))
        elif pricing_type in ('hourly', 'per_hour'):
            return strategy_class(
                minimum_hours=kwargs.get('minimum_hours', 1),
                rounding_interval=kwargs.get('rounding_interval', 30)
            )
        elif pricing_type in ('daily', 'per_day'):
            return strategy_class(
                minimum_days=kwargs.get('minimum_days', 1),
                weekly_discount=Decimal(str(kwargs.get('weekly_discount', '0.10'))),
                monthly_discount=Decimal(str(kwargs.get('monthly_discount', '0.20')))
            )
        elif pricing_type in ('distance', 'per_km'):
            return strategy_class(
                base_fee=Decimal(str(kwargs.get('base_fee', '0'))),
                free_km=kwargs.get('free_km', 0),
                max_distance=kwargs.get('max_distance')
            )
        elif pricing_type in ('weight', 'per_ton', 'per_m3'):
            return strategy_class(
                minimum_weight=Decimal(str(kwargs.get('minimum_weight', '0'))),
                weight_unit=kwargs.get('weight_unit', 'ton')
            )

        return strategy_class()


# ===========================================
# خدمة حساب الأسعار
# ===========================================

@dataclass
class PricingResult:
    """نتيجة حساب السعر"""
    items_total: Decimal
    delivery_total: Decimal
    subtotal: Decimal
    tax_amount: Decimal
    platform_fee: Decimal
    total: Decimal
    vendor_payout: Decimal
    driver_payout: Decimal
    platform_revenue: Decimal
    breakdown: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'items_total': float(self.items_total),
            'delivery_total': float(self.delivery_total),
            'subtotal': float(self.subtotal),
            'tax_amount': float(self.tax_amount),
            'platform_fee': float(self.platform_fee),
            'total': float(self.total),
            'vendor_payout': float(self.vendor_payout),
            'driver_payout': float(self.driver_payout),
            'platform_revenue': float(self.platform_revenue),
            'breakdown': self.breakdown,
        }


class PricingService:
    """
    خدمة حساب الأسعار الشاملة
    تدعم جميع أنواع التسعير المرنة
    """

    def __init__(self):
        self.tax_rate = Decimal(str(getattr(settings, 'TAX_RATE', '0.15')))  # ضريبة القيمة المضافة السعودية

    def calculate_item_price(
        self,
        pricing_type: str,
        base_price: Decimal,
        quantity: Decimal,
        context: Optional[Dict[str, Any]] = None,
        **strategy_kwargs
    ) -> Tuple[Decimal, Dict[str, Any]]:
        """حساب سعر منتج واحد"""
        context = context or {}
        strategy = PricingStrategyFactory.get_strategy(pricing_type, **strategy_kwargs)

        price = strategy.calculate(base_price, quantity, context)
        breakdown = strategy.get_breakdown(base_price, quantity, context)

        return price, breakdown

    def calculate_delivery_price(
        self,
        delivery_type: str,
        base_rate: Decimal,
        context: Dict[str, Any],
        **kwargs
    ) -> Tuple[Decimal, Dict[str, Any]]:
        """حساب سعر التوصيل"""

        if delivery_type == 'free' or delivery_type == 'merchant':
            return Decimal('0'), {'type': 'free', 'reason': 'توصيل مجاني من التاجر', 'total': 0}

        if delivery_type == 'pickup':
            return Decimal('0'), {'type': 'pickup', 'reason': 'استلام من الموقع', 'total': 0}

        strategy = PricingStrategyFactory.get_strategy(delivery_type, **kwargs)
        price = strategy.calculate(base_rate, Decimal('1'), context)
        breakdown = strategy.get_breakdown(base_rate, Decimal('1'), context)

        return price, breakdown

    def calculate_order_total(
        self,
        items: List[Dict[str, Any]],
        delivery_info: Optional[Dict[str, Any]] = None,
        vendor_commission_rate: Decimal = Decimal('0.05'),
        driver_commission_rate: Decimal = Decimal('0.15'),
        include_tax: bool = True
    ) -> PricingResult:
        """
        حساب إجمالي الطلب مع كل التفاصيل

        items: قائمة المنتجات، كل منتج يحتوي على:
            - pricing_type: نوع التسعير
            - base_price: السعر الأساسي
            - quantity: الكمية
            - context: سياق إضافي (ساعات، أيام، إلخ)
            - strategy_kwargs: معاملات الاستراتيجية

        delivery_info: معلومات التوصيل
            - type: نوع التوصيل
            - base_rate: السعر الأساسي
            - context: المسافة، الوزن، إلخ
        """
        items_breakdown = []
        items_total = Decimal('0')

        # حساب أسعار المنتجات
        for item in items:
            price, breakdown = self.calculate_item_price(
                pricing_type=item.get('pricing_type', 'fixed'),
                base_price=Decimal(str(item['base_price'])),
                quantity=Decimal(str(item.get('quantity', 1))),
                context=item.get('context', {}),
                **item.get('strategy_kwargs', {})
            )
            items_total += price
            items_breakdown.append({
                'item_id': item.get('id'),
                'name': item.get('name'),
                'price': float(price),
                **breakdown
            })

        # حساب التوصيل
        delivery_total = Decimal('0')
        delivery_breakdown = {'type': 'not_applicable', 'total': 0}

        if delivery_info:
            delivery_total, delivery_breakdown = self.calculate_delivery_price(
                delivery_type=delivery_info.get('type', 'free'),
                base_rate=Decimal(str(delivery_info.get('base_rate', 0))),
                context=delivery_info.get('context', {}),
                **delivery_info.get('kwargs', {})
            )

        # المجموع الفرعي
        subtotal = items_total + delivery_total

        # الضريبة
        tax_amount = Decimal('0')
        if include_tax:
            tax_amount = (subtotal * self.tax_rate).quantize(Decimal('0.01'))

        # الإجمالي النهائي
        total = subtotal + tax_amount

        # حساب التوزيعات
        vendor_commission = (items_total * vendor_commission_rate).quantize(Decimal('0.01'))
        driver_commission = (delivery_total * driver_commission_rate).quantize(Decimal('0.01'))

        vendor_payout = items_total - vendor_commission
        driver_payout = delivery_total - driver_commission
        platform_revenue = vendor_commission + driver_commission

        breakdown = {
            'items': items_breakdown,
            'delivery': delivery_breakdown,
            'tax_rate': float(self.tax_rate * 100),
            'vendor_commission_rate': float(vendor_commission_rate * 100),
            'driver_commission_rate': float(driver_commission_rate * 100),
        }

        return PricingResult(
            items_total=items_total,
            delivery_total=delivery_total,
            subtotal=subtotal,
            tax_amount=tax_amount,
            platform_fee=platform_revenue,
            total=total,
            vendor_payout=vendor_payout,
            driver_payout=driver_payout,
            platform_revenue=platform_revenue,
            breakdown=breakdown
        )


# ===========================================
# محرك التسوية - Reconciliation Engine
# ===========================================

@dataclass
class ReconciliationResult:
    """نتيجة عملية التسوية"""
    status: str  # matched, discrepancy, missing_in_source, missing_in_target
    our_amount: Optional[Decimal]
    provider_amount: Optional[Decimal]
    difference: Optional[Decimal]
    transaction_id: str
    provider_reference: Optional[str]
    details: Dict[str, Any] = field(default_factory=dict)


class ReconciliationEngine:
    """
    محرك التسوية المالية

    يقارن بياناتنا مع بيانات مزود الدفع (Tap)
    ويكتشف التناقضات ويسجلها للمراجعة
    """

    def __init__(self, tolerance: Decimal = Decimal('0.01')):
        self.tolerance = tolerance  # هامش الخطأ المقبول

    def reconcile_transaction(
        self,
        our_record: Dict[str, Any],
        provider_record: Optional[Dict[str, Any]]
    ) -> ReconciliationResult:
        """تسوية معاملة واحدة"""

        transaction_id = our_record.get('transaction_id')
        our_amount = Decimal(str(our_record.get('amount', 0)))

        # حالة: المعاملة موجودة عندنا فقط
        if not provider_record:
            return ReconciliationResult(
                status='missing_in_provider',
                our_amount=our_amount,
                provider_amount=None,
                difference=our_amount,
                transaction_id=transaction_id,
                provider_reference=None,
                details={'reason': 'المعاملة غير موجودة عند مزود الدفع'}
            )

        provider_amount = Decimal(str(provider_record.get('amount', 0)))
        provider_ref = provider_record.get('reference')
        difference = our_amount - provider_amount

        # التحقق من التطابق مع هامش الخطأ
        if abs(difference) <= self.tolerance:
            return ReconciliationResult(
                status='matched',
                our_amount=our_amount,
                provider_amount=provider_amount,
                difference=difference,
                transaction_id=transaction_id,
                provider_reference=provider_ref,
                details={'matched_at': timezone.now().isoformat()}
            )

        # يوجد تناقض
        return ReconciliationResult(
            status='discrepancy',
            our_amount=our_amount,
            provider_amount=provider_amount,
            difference=difference,
            transaction_id=transaction_id,
            provider_reference=provider_ref,
            details={
                'discrepancy_type': 'amount_mismatch',
                'discrepancy_percentage': float(abs(difference) / our_amount * 100) if our_amount else 0
            }
        )

    def reconcile_batch(
        self,
        our_records: List[Dict[str, Any]],
        provider_records: List[Dict[str, Any]],
        match_key: str = 'transaction_id'
    ) -> Dict[str, Any]:
        """تسوية دفعة من المعاملات"""

        # فهرسة سجلات المزود
        provider_index = {
            r.get(match_key): r for r in provider_records
        }

        results = {
            'matched': [],
            'discrepancies': [],
            'missing_in_provider': [],
            'missing_in_our_system': [],
            'summary': {
                'total_our_records': len(our_records),
                'total_provider_records': len(provider_records),
                'matched_count': 0,
                'discrepancy_count': 0,
                'our_total_amount': Decimal('0'),
                'provider_total_amount': Decimal('0'),
                'total_difference': Decimal('0'),
            }
        }

        processed_provider_keys = set()

        # معالجة سجلاتنا
        for our_record in our_records:
            key = our_record.get(match_key)
            provider_record = provider_index.get(key)

            result = self.reconcile_transaction(our_record, provider_record)

            results['summary']['our_total_amount'] += result.our_amount or Decimal('0')

            if provider_record:
                processed_provider_keys.add(key)
                results['summary']['provider_total_amount'] += result.provider_amount or Decimal('0')

            if result.status == 'matched':
                results['matched'].append(result)
                results['summary']['matched_count'] += 1
            elif result.status == 'discrepancy':
                results['discrepancies'].append(result)
                results['summary']['discrepancy_count'] += 1
                results['summary']['total_difference'] += abs(result.difference or Decimal('0'))
            else:
                results['missing_in_provider'].append(result)

        # البحث عن سجلات موجودة عند المزود فقط
        for key, provider_record in provider_index.items():
            if key not in processed_provider_keys:
                results['missing_in_our_system'].append(ReconciliationResult(
                    status='missing_in_our_system',
                    our_amount=None,
                    provider_amount=Decimal(str(provider_record.get('amount', 0))),
                    difference=None,
                    transaction_id=str(key),
                    provider_reference=provider_record.get('reference'),
                    details={'reason': 'المعاملة موجودة عند المزود فقط'}
                ))

        return results

    def generate_report(self, reconciliation_results: Dict[str, Any]) -> Dict[str, Any]:
        """إنشاء تقرير التسوية"""
        summary = reconciliation_results['summary']

        match_rate = (
            (summary['matched_count'] / summary['total_our_records'] * 100)
            if summary['total_our_records'] > 0 else 0
        )

        return {
            'report_date': timezone.now().isoformat(),
            'match_rate': f"{match_rate:.2f}%",
            'total_transactions': summary['total_our_records'],
            'matched_transactions': summary['matched_count'],
            'discrepancies': summary['discrepancy_count'],
            'missing_in_provider': len(reconciliation_results['missing_in_provider']),
            'missing_in_our_system': len(reconciliation_results['missing_in_our_system']),
            'our_total': float(summary['our_total_amount']),
            'provider_total': float(summary['provider_total_amount']),
            'total_difference': float(summary['total_difference']),
            'requires_investigation': summary['discrepancy_count'] > 0 or
                                     len(reconciliation_results['missing_in_provider']) > 0 or
                                     len(reconciliation_results['missing_in_our_system']) > 0,
        }


# ===========================================
# خدمة العمولات
# ===========================================

class CommissionService:
    """خدمة حساب وإدارة العمولات"""

    def __init__(self):
        self.default_vendor_rate = Decimal('0.05')  # 5%
        self.default_driver_rate = Decimal('0.15')  # 15%

    def get_vendor_commission_rate(
        self,
        vendor_id: str,
        category_id: Optional[str] = None,
        order_amount: Optional[Decimal] = None
    ) -> Decimal:
        """
        الحصول على نسبة عمولة التاجر
        يمكن أن تكون مخصصة حسب التاجر أو القسم أو حجم الطلب
        """
        # في المستقبل: جلب من قاعدة البيانات
        # CommissionRule.objects.filter(...)

        cache_key = f"vendor_commission:{vendor_id}:{category_id}"
        cached_rate = cache.get(cache_key)

        if cached_rate:
            return Decimal(str(cached_rate))

        # منطق التسعير المتدرج للتجار الكبار
        if order_amount and order_amount >= Decimal('100000'):
            rate = Decimal('0.03')  # 3% للطلبات الكبيرة جداً
        elif order_amount and order_amount >= Decimal('50000'):
            rate = Decimal('0.04')  # 4% للطلبات الكبيرة
        else:
            rate = self.default_vendor_rate

        cache.set(cache_key, str(rate), timeout=3600)
        return rate

    def get_driver_commission_rate(
        self,
        driver_id: str,
        delivery_type: Optional[str] = None
    ) -> Decimal:
        """الحصول على نسبة عمولة السائق"""
        # في المستقبل: جلب من قاعدة البيانات بناءً على نوع التوصيل
        return self.default_driver_rate

    def calculate_split(
        self,
        order_amount: Decimal,
        delivery_amount: Decimal,
        vendor_id: str,
        driver_id: Optional[str] = None,
        category_id: Optional[str] = None
    ) -> Dict[str, Decimal]:
        """
        حساب توزيع المبالغ بين الأطراف
        هذا ما نسجله للمقارنة مع Tap Connect
        """
        vendor_rate = self.get_vendor_commission_rate(
            vendor_id, category_id, order_amount
        )

        vendor_commission = (order_amount * vendor_rate).quantize(Decimal('0.01'))
        vendor_payout = order_amount - vendor_commission

        driver_payout = Decimal('0')
        driver_commission = Decimal('0')

        if driver_id and delivery_amount > 0:
            driver_rate = self.get_driver_commission_rate(driver_id)
            driver_commission = (delivery_amount * driver_rate).quantize(Decimal('0.01'))
            driver_payout = delivery_amount - driver_commission

        platform_revenue = vendor_commission + driver_commission

        return {
            'order_amount': order_amount,
            'delivery_amount': delivery_amount,
            'vendor_commission': vendor_commission,
            'vendor_payout': vendor_payout,
            'driver_commission': driver_commission,
            'driver_payout': driver_payout,
            'platform_revenue': platform_revenue,
            'total_collected': order_amount + delivery_amount,
        }


# ===========================================
# خدمة السجل المالي (Ledger)
# ===========================================

class LedgerService:
    """
    خدمة السجل المالي غير القابل للتعديل
    كل عملية مالية تُسجل هنا للتدقيق
    """

    @staticmethod
    def generate_checksum(data: Dict[str, Any]) -> str:
        """توليد checksum للتحقق من سلامة البيانات"""
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()

    @staticmethod
    def verify_checksum(entry_data: Dict[str, Any], stored_checksum: str) -> bool:
        """التحقق من صحة checksum"""
        calculated = LedgerService.generate_checksum(entry_data)
        return hmac.compare_digest(calculated, stored_checksum)

    def record_transaction(
        self,
        transaction_type: str,
        amount: Decimal,
        currency: str,
        debit_account: str,
        credit_account: str,
        reference_type: str,
        reference_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        تسجيل معاملة في السجل
        Double-entry bookkeeping pattern
        """
        from .models import LedgerEntry

        timestamp = timezone.now()

        entry_data = {
            'transaction_type': transaction_type,
            'amount': str(amount),
            'currency': currency,
            'debit_account': debit_account,
            'credit_account': credit_account,
            'reference_type': reference_type,
            'reference_id': reference_id,
            'timestamp': timestamp.isoformat(),
            'metadata': metadata or {},
        }

        checksum = self.generate_checksum(entry_data)

        with transaction.atomic():
            # الحصول على hash السجل السابق للتسلسل
            previous_entry = LedgerEntry.objects.order_by('-created_at').first()
            previous_hash = previous_entry.checksum if previous_entry else '0' * 64

            # إضافة hash السابق للتسلسل
            entry_data['previous_hash'] = previous_hash
            checksum = self.generate_checksum(entry_data)

            entry = LedgerEntry.objects.create(
                transaction_type=transaction_type,
                amount=amount,
                currency=currency,
                debit_account=debit_account,
                credit_account=credit_account,
                reference_type=reference_type,
                reference_id=reference_id,
                metadata=metadata or {},
                checksum=checksum,
            )

        logger.info(
            f"Ledger entry created: {entry.id} - {transaction_type} - {amount} {currency}"
        )

        return {
            'ledger_id': str(entry.id),
            'checksum': checksum,
            'timestamp': timestamp.isoformat(),
        }

    def verify_chain_integrity(self, start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        التحقق من سلامة سلسلة السجلات
        يكتشف أي تلاعب في السجلات
        """
        from .models import LedgerEntry

        queryset = LedgerEntry.objects.order_by('created_at')

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        entries = list(queryset)

        if not entries:
            return {'valid': True, 'checked': 0, 'errors': []}

        errors = []
        previous_hash = '0' * 64

        for i, entry in enumerate(entries):
            # إعادة بناء بيانات السجل
            entry_data = {
                'transaction_type': entry.transaction_type,
                'amount': str(entry.amount),
                'currency': entry.currency,
                'debit_account': entry.debit_account,
                'credit_account': entry.credit_account,
                'reference_type': entry.reference_type,
                'reference_id': entry.reference_id,
                'timestamp': entry.created_at.isoformat(),
                'metadata': entry.metadata,
                'previous_hash': previous_hash,
            }

            calculated_checksum = self.generate_checksum(entry_data)

            if not hmac.compare_digest(calculated_checksum, entry.checksum):
                errors.append({
                    'entry_id': str(entry.id),
                    'position': i,
                    'error': 'checksum_mismatch',
                    'expected': calculated_checksum,
                    'found': entry.checksum,
                })

            previous_hash = entry.checksum

        return {
            'valid': len(errors) == 0,
            'checked': len(entries),
            'errors': errors,
            'verification_date': timezone.now().isoformat(),
        }


# ===========================================
# خدمة الفواتير
# ===========================================

class InvoiceService:
    """
    خدمة إنشاء الفواتير
    متوافقة مع متطلبات ZATCA للفوترة الإلكترونية
    """

    def __init__(self):
        self.sequence_counter_key = 'invoice:sequence:counter'

    def generate_invoice_number(self, prefix: str = 'INV') -> str:
        """توليد رقم فاتورة فريد"""
        # استخدام Redis للعداد التسلسلي
        try:
            from django_redis import get_redis_connection
            redis_conn = get_redis_connection("default")
            sequence = redis_conn.incr(self.sequence_counter_key)
        except Exception:
            # fallback إلى UUID إذا Redis غير متاح
            import uuid
            sequence = str(uuid.uuid4().int)[:8]

        date_part = timezone.now().strftime('%Y%m%d')
        return f"{prefix}-{date_part}-{sequence:08d}"

    def create_invoice(
        self,
        order_id: str,
        customer_info: Dict[str, Any],
        vendor_info: Dict[str, Any],
        line_items: List[Dict[str, Any]],
        delivery_info: Optional[Dict[str, Any]] = None,
        tax_rate: Decimal = Decimal('0.15')
    ) -> Dict[str, Any]:
        """
        إنشاء فاتورة جديدة

        في المستقبل: هذه البيانات ترسل لبرنامج المحاسبة (Qoyod/Dafater)
        الذي يتولى الربط مع ZATCA
        """
        invoice_number = self.generate_invoice_number()
        invoice_date = timezone.now()

        # حساب المجاميع
        subtotal = Decimal('0')
        items = []

        for item in line_items:
            item_total = Decimal(str(item['price'])) * Decimal(str(item['quantity']))
            subtotal += item_total
            items.append({
                **item,
                'total': float(item_total),
            })

        # إضافة التوصيل إن وجد
        delivery_total = Decimal('0')
        if delivery_info and delivery_info.get('amount'):
            delivery_total = Decimal(str(delivery_info['amount']))

        # حساب الضريبة
        taxable_amount = subtotal + delivery_total
        tax_amount = (taxable_amount * tax_rate).quantize(Decimal('0.01'))
        total = taxable_amount + tax_amount

        invoice_data = {
            'invoice_number': invoice_number,
            'invoice_date': invoice_date.isoformat(),
            'order_id': order_id,
            'status': 'draft',

            # معلومات البائع
            'vendor': {
                'id': vendor_info.get('id'),
                'name': vendor_info.get('name'),
                'vat_number': vendor_info.get('vat_number'),
                'cr_number': vendor_info.get('cr_number'),
                'address': vendor_info.get('address'),
            },

            # معلومات المشتري
            'customer': {
                'id': customer_info.get('id'),
                'name': customer_info.get('name'),
                'vat_number': customer_info.get('vat_number'),
                'phone': customer_info.get('phone'),
                'address': customer_info.get('address'),
            },

            # البنود
            'line_items': items,

            # التوصيل
            'delivery': {
                'amount': float(delivery_total),
                'description': delivery_info.get('description', 'رسوم التوصيل') if delivery_info else None,
            } if delivery_total > 0 else None,

            # المجاميع
            'subtotal': float(subtotal),
            'delivery_total': float(delivery_total),
            'taxable_amount': float(taxable_amount),
            'tax_rate': float(tax_rate * 100),
            'tax_amount': float(tax_amount),
            'total': float(total),

            # بيانات ZATCA (ستملأ من برنامج المحاسبة)
            'zatca': {
                'status': 'pending',
                'submission_date': None,
                'clearance_status': None,
                'qr_code': None,
            }
        }

        return invoice_data


# ===========================================
# تصدير الخدمات
# ===========================================

pricing_service = PricingService()
commission_service = CommissionService()
reconciliation_engine = ReconciliationEngine()
ledger_service = LedgerService()
invoice_service = InvoiceService()
