"""
خدمات نظام الطلبات
==================

خدمات إدارة الطلبات والتوصيل
"""

import uuid
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass

from django.conf import settings
from django.db import transaction
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone

from .models import (
    Order,
    OrderItem,
    OrderStatus,
    PaymentStatus,
    OrderType,
    DeliveryType,
    OrderDelivery,
    OrderStatusHistory,
    OrderReview,
    OrderRefund,
    CancellationReason,
)


@dataclass
class OrderResult:
    """نتيجة عملية الطلب"""
    success: bool
    order: Optional[Order] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    payment_url: Optional[str] = None


@dataclass
class OrderTotals:
    """مجاميع الطلب"""
    subtotal: Decimal
    delivery_fee: Decimal
    service_fee: Decimal
    discount: Decimal
    coupon_discount: Decimal
    tax: Decimal
    total: Decimal


# =============================================
# خدمة الطلبات
# =============================================

class OrderService:
    """خدمة إدارة الطلبات الرئيسية"""

    def create_order(
        self,
        customer,
        vendor_id: str,
        items: List[Dict[str, Any]],
        delivery_address_id: Optional[str] = None,
        delivery_type: str = 'standard',
        delivery_notes: str = '',
        scheduled_delivery_date=None,
        scheduled_delivery_time: str = '',
        payment_method: str = 'card',
        coupon_code: str = '',
        customer_notes: str = '',
        service_date=None,
        service_time=None,
        rental_start_date=None,
        rental_end_date=None,
        ip_address: str = '',
        source: str = 'app',
    ) -> OrderResult:
        """
        إنشاء طلب جديد

        يتحقق من توفر المنتجات ويحسب الأسعار
        """
        from apps.stores.models import Store
        from apps.products.models import Product, ProductVariant, ProductOptionValue
        from apps.users.models import UserAddress

        # التحقق من المتجر
        try:
            vendor = Store.objects.get(id=vendor_id, is_active=True)
        except Store.DoesNotExist:
            return OrderResult(
                success=False,
                error='المتجر غير موجود أو غير نشط',
                error_code='vendor_not_found'
            )

        # التحقق من العنوان
        delivery_address = None
        if delivery_address_id and delivery_type != DeliveryType.PICKUP:
            try:
                delivery_address = UserAddress.objects.get(
                    id=delivery_address_id,
                    user=customer
                )
            except UserAddress.DoesNotExist:
                return OrderResult(
                    success=False,
                    error='عنوان التوصيل غير موجود',
                    error_code='address_not_found'
                )

        # تحديد نوع الطلب
        order_type = self._determine_order_type(items)

        with transaction.atomic():
            # إنشاء الطلب
            order = Order.objects.create(
                customer=customer,
                vendor=vendor,
                order_type=order_type,
                status=OrderStatus.DRAFT,
                payment_method=payment_method,
                delivery_type=delivery_type,
                delivery_address=delivery_address,
                delivery_notes=delivery_notes,
                scheduled_delivery_date=scheduled_delivery_date,
                scheduled_delivery_time=scheduled_delivery_time,
                customer_notes=customer_notes,
                coupon_code=coupon_code,
                service_date=service_date,
                service_time=service_time,
                rental_start_date=rental_start_date,
                rental_end_date=rental_end_date,
                ip_address=ip_address,
                source=source,
            )

            # إضافة العناصر
            for item_data in items:
                product_id = item_data.get('product_id')
                variant_id = item_data.get('variant_id')
                quantity = Decimal(str(item_data.get('quantity', 1)))
                selected_options = item_data.get('selected_options', {})
                rental_days = item_data.get('rental_days', 0)
                rental_hours = item_data.get('rental_hours', 0)
                service_details = item_data.get('service_details', {})

                # جلب المنتج
                try:
                    product = Product.objects.get(id=product_id)
                except Product.DoesNotExist:
                    order.delete()
                    return OrderResult(
                        success=False,
                        error=f'المنتج غير موجود: {product_id}',
                        error_code='product_not_found'
                    )

                # التحقق من التوفر
                if not product.is_available:
                    order.delete()
                    return OrderResult(
                        success=False,
                        error=f'المنتج غير متاح: {product.name}',
                        error_code='product_unavailable'
                    )

                # جلب المتغير إن وجد
                variant = None
                if variant_id:
                    try:
                        variant = ProductVariant.objects.get(
                            id=variant_id,
                            product=product
                        )
                    except ProductVariant.DoesNotExist:
                        pass

                # حساب السعر
                unit_price = variant.price if variant else product.price

                # حساب سعر الخيارات
                options_price = Decimal('0')
                if selected_options:
                    for option_id, value_id in selected_options.items():
                        try:
                            option_value = ProductOptionValue.objects.get(
                                id=value_id,
                                option__product=product
                            )
                            options_price += option_value.price_adjustment
                        except ProductOptionValue.DoesNotExist:
                            pass

                # حساب السعر للتأجير
                if rental_days > 0 or rental_hours > 0:
                    unit_price = self._calculate_rental_price(
                        product, rental_days, rental_hours
                    )

                # حساب الإجمالي
                total_price = (unit_price + options_price) * quantity

                # إنشاء عنصر الطلب
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    variant=variant,
                    unit_price=unit_price,
                    quantity=quantity,
                    total_price=total_price,
                    pricing_type=product.pricing_type,
                    selected_options=selected_options,
                    options_price=options_price,
                    rental_days=rental_days,
                    rental_hours=rental_hours,
                    service_details=service_details,
                )

            # حساب رسوم التوصيل
            order.delivery_fee = self._calculate_delivery_fee(
                order, delivery_type, delivery_address
            )

            # تطبيق الكوبون
            if coupon_code:
                coupon_discount = self._apply_coupon(order, coupon_code)
                order.coupon_discount = coupon_discount

            # حساب العمولات
            self._calculate_commissions(order, vendor)

            # حساب المجاميع
            order.calculate_totals()
            order.save()

            # إنشاء سجل التوصيل
            if delivery_type != DeliveryType.PICKUP:
                OrderDelivery.objects.create(
                    order=order,
                    estimated_distance_km=self._estimate_distance(
                        vendor, delivery_address
                    ) if delivery_address else None,
                )

            # تسجيل الحالة
            OrderStatusHistory.objects.create(
                order=order,
                status=OrderStatus.DRAFT,
                changed_by=customer,
                notes='تم إنشاء الطلب'
            )

        return OrderResult(
            success=True,
            order=order
        )

    def place_order(self, order: Order, user) -> OrderResult:
        """
        تأكيد الطلب وبدء عملية الدفع

        ينقل الطلب من مسودة إلى بانتظار الدفع
        """
        if order.status != OrderStatus.DRAFT:
            return OrderResult(
                success=False,
                error='الطلب ليس في حالة المسودة',
                error_code='invalid_status'
            )

        # التحقق من توفر المنتجات مرة أخرى
        for item in order.items.all():
            if not item.product.is_available:
                return OrderResult(
                    success=False,
                    error=f'المنتج غير متاح: {item.product.name}',
                    error_code='product_unavailable'
                )

        # تحديث الحالة
        order.update_status(OrderStatus.PENDING_PAYMENT, user, 'بانتظار الدفع')
        order.placed_at = timezone.now()
        order.save(update_fields=['placed_at'])

        # إنشاء رابط الدفع
        payment_url = self._create_payment_session(order)

        return OrderResult(
            success=True,
            order=order,
            payment_url=payment_url
        )

    def confirm_payment(
        self,
        order: Order,
        transaction_id: str,
        amount: Decimal
    ) -> OrderResult:
        """
        تأكيد الدفع

        يُستدعى من webhook بوابة الدفع
        """
        if order.payment_status == PaymentStatus.PAID:
            return OrderResult(success=True, order=order)

        order.paid_amount = amount
        order.payment_status = PaymentStatus.PAID

        # تحديث حالة الطلب
        if order.status == OrderStatus.PENDING_PAYMENT:
            order.update_status(OrderStatus.CONFIRMED, notes='تم الدفع بنجاح')

        order.save()

        # إنشاء المعاملة المالية
        self._create_transaction(order, transaction_id, amount)

        # إرسال إشعارات
        self._send_order_notifications(order, 'confirmed')

        return OrderResult(success=True, order=order)

    def accept_order(self, order: Order, vendor_user) -> OrderResult:
        """
        قبول الطلب من التاجر
        """
        if order.status not in [OrderStatus.CONFIRMED, OrderStatus.PENDING]:
            return OrderResult(
                success=False,
                error='لا يمكن قبول الطلب في هذه الحالة',
                error_code='invalid_status'
            )

        order.update_status(
            OrderStatus.ACCEPTED,
            vendor_user,
            'تم قبول الطلب من التاجر'
        )

        # إرسال إشعار للعميل
        self._send_order_notifications(order, 'accepted')

        return OrderResult(success=True, order=order)

    def update_status(
        self,
        order: Order,
        new_status: str,
        user,
        notes: str = ''
    ) -> OrderResult:
        """
        تحديث حالة الطلب
        """
        # التحقق من صحة التحويل
        valid_transitions = self._get_valid_transitions(order.status)

        if new_status not in valid_transitions:
            return OrderResult(
                success=False,
                error=f'لا يمكن تحويل الحالة من {order.status} إلى {new_status}',
                error_code='invalid_transition'
            )

        order.update_status(new_status, user, notes)

        # إرسال إشعارات
        self._send_order_notifications(order, new_status)

        return OrderResult(success=True, order=order)

    def cancel_order(
        self,
        order: Order,
        user,
        reason: str,
        notes: str = ''
    ) -> OrderResult:
        """
        إلغاء الطلب
        """
        if not order.can_cancel:
            return OrderResult(
                success=False,
                error='لا يمكن إلغاء هذا الطلب',
                error_code='cannot_cancel'
            )

        order.cancellation_reason = reason
        order.cancellation_notes = notes
        order.cancelled_by = user
        order.update_status(OrderStatus.CANCELLED, user, notes)

        # معالجة الاسترداد إذا كان مدفوعاً
        if order.is_paid:
            self._process_refund(order, order.paid_amount, user)

        # إرسال إشعارات
        self._send_order_notifications(order, 'cancelled')

        return OrderResult(success=True, order=order)

    def get_order_stats(
        self,
        user,
        user_type: str = 'customer',
        vendor_id: Optional[str] = None,
        start_date=None,
        end_date=None
    ) -> Dict[str, Any]:
        """
        إحصائيات الطلبات
        """
        if user_type == 'customer':
            queryset = Order.objects.filter(customer=user)
        else:  # vendor
            from apps.stores.models import Store
            store = Store.objects.filter(id=vendor_id).first()
            if not store:
                return {}
            queryset = Order.objects.filter(vendor=store)

        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)

        stats = queryset.aggregate(
            total_orders=Count('id'),
            total_revenue=Sum('total_amount'),
            avg_order_value=Avg('total_amount'),
        )

        # إحصائيات حسب الحالة
        status_counts = queryset.values('status').annotate(
            count=Count('id')
        )

        status_dict = {s['status']: s['count'] for s in status_counts}

        return {
            'total_orders': stats.get('total_orders') or 0,
            'total_revenue': float(stats.get('total_revenue') or 0),
            'average_order_value': float(stats.get('avg_order_value') or 0),
            'pending_orders': status_dict.get(OrderStatus.PENDING, 0),
            'processing_orders': status_dict.get(OrderStatus.PROCESSING, 0),
            'completed_orders': status_dict.get(OrderStatus.COMPLETED, 0),
            'cancelled_orders': status_dict.get(OrderStatus.CANCELLED, 0),
        }

    # =============================================
    # الدوال المساعدة
    # =============================================

    def _determine_order_type(self, items: List[Dict]) -> str:
        """تحديد نوع الطلب بناءً على العناصر"""
        # TODO: تحليل العناصر لتحديد النوع
        return OrderType.PRODUCT

    def _calculate_delivery_fee(
        self,
        order: Order,
        delivery_type: str,
        address
    ) -> Decimal:
        """حساب رسوم التوصيل"""
        if delivery_type == DeliveryType.PICKUP:
            return Decimal('0')

        # رسوم أساسية
        base_fees = {
            DeliveryType.STANDARD: Decimal('25'),
            DeliveryType.EXPRESS: Decimal('45'),
            DeliveryType.SAME_DAY: Decimal('60'),
            DeliveryType.CRANE: Decimal('200'),
            DeliveryType.TRUCK: Decimal('150'),
        }

        base_fee = base_fees.get(delivery_type, Decimal('25'))

        # إضافة رسوم حسب المسافة
        # TODO: حساب المسافة وإضافة الرسوم

        return base_fee

    def _apply_coupon(self, order: Order, coupon_code: str) -> Decimal:
        """تطبيق كوبون الخصم"""
        # TODO: التحقق من صلاحية الكوبون وتطبيقه
        return Decimal('0')

    def _calculate_commissions(self, order: Order, vendor):
        """حساب العمولات"""
        from apps.finance.services import commission_service

        vendor_rate = commission_service.get_vendor_commission_rate(
            vendor_id=str(vendor.id),
            order_amount=order.subtotal
        )

        order.vendor_commission = (order.subtotal * vendor_rate).quantize(Decimal('0.01'))
        order.platform_commission = order.vendor_commission

    def _calculate_rental_price(
        self,
        product,
        days: int,
        hours: int
    ) -> Decimal:
        """حساب سعر التأجير"""
        daily_rate = product.pricing_config.get('daily_rate', product.price)
        hourly_rate = product.pricing_config.get('hourly_rate', product.price / 8)

        total = (Decimal(str(daily_rate)) * days) + (Decimal(str(hourly_rate)) * hours)
        return total

    def _estimate_distance(self, vendor, address) -> Decimal:
        """تقدير المسافة"""
        if not vendor.location or not address.location:
            return Decimal('10')

        # حساب المسافة الفعلية
        distance = vendor.location.distance(address.location)
        return Decimal(str(distance.km)).quantize(Decimal('0.01'))

    def _create_payment_session(self, order: Order) -> str:
        """
        إنشاء جلسة دفع مع Tap Payment

        يدعم:
        - وضع الاختبار (TEST_MODE)
        - وضع الإنتاج (LIVE_MODE)
        """
        import requests
        import logging

        logger = logging.getLogger(__name__)

        tap_config = getattr(settings, 'TAP_PAYMENT_CONFIG', {})
        test_mode = tap_config.get('TEST_MODE', settings.DEBUG)

        # وضع الاختبار - رابط وهمي يعمل
        if test_mode:
            # إنشاء جلسة اختبار محلية
            from django.core.cache import cache
            import uuid

            session_id = str(uuid.uuid4())
            cache.set(
                f'payment_session:{session_id}',
                {
                    'order_id': str(order.id),
                    'amount': str(order.total_amount),
                    'status': 'pending',
                    'test_mode': True,
                },
                timeout=3600  # ساعة
            )

            # رابط الدفع الاختباري
            base_url = tap_config.get('CALLBACK_BASE_URL', 'http://localhost:8000')
            payment_url = f'{base_url}/api/payments/test/{session_id}/'

            logger.info(f'[TAP TEST] Payment session created: {session_id} for order {order.id}')
            print(f'╔══════════════════════════════════════════╗')
            print(f'║ 💳 PAYMENT TEST MODE                     ║')
            print(f'║ Order: {str(order.id)[:30]:<30} ║')
            print(f'║ Amount: {order.total_amount:<30} SAR ║')
            print(f'║ Session: {session_id[:28]:<28} ║')
            print(f'╚══════════════════════════════════════════╝')

            return payment_url

        # الإنتاج - Tap Payment API
        api_key = tap_config.get('SECRET_KEY')
        if not api_key:
            logger.error('TAP_PAYMENT_CONFIG.SECRET_KEY not configured')
            raise ValueError('Payment gateway not configured')

        # إعداد بيانات الدفع
        callback_url = tap_config.get('CALLBACK_URL', 'https://api.diwani.sa/payments/callback/')
        redirect_url = tap_config.get('REDIRECT_URL', 'https://diwani.sa/payment/result/')

        payload = {
            'amount': float(order.total_amount),
            'currency': 'SAR',
            'threeDSecure': True,
            'save_card': False,
            'description': f'طلب رقم {order.order_number or order.id}',
            'statement_descriptor': 'DIWANI',
            'metadata': {
                'order_id': str(order.id),
                'customer_id': str(order.customer_id),
            },
            'reference': {
                'transaction': str(order.id),
                'order': order.order_number or str(order.id),
            },
            'receipt': {
                'email': True,
                'sms': True,
            },
            'customer': {
                'first_name': order.customer.first_name or 'عميل',
                'last_name': order.customer.last_name or '',
                'email': order.customer.email or '',
                'phone': {
                    'country_code': '966',
                    'number': str(order.customer.phone_number).replace('+966', '').replace('+', ''),
                },
            },
            'source': {
                'id': 'src_all',  # يقبل جميع طرق الدفع
            },
            'redirect': {
                'url': redirect_url,
            },
            'post': {
                'url': callback_url,
            },
        }

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }

        try:
            response = requests.post(
                'https://api.tap.company/v2/charges',
                json=payload,
                headers=headers,
                timeout=30,
            )

            result = response.json()

            if response.status_code == 200 and 'transaction' in result:
                payment_url = result.get('transaction', {}).get('url', '')
                charge_id = result.get('id', '')

                # حفظ معرف العملية
                order.payment_reference = charge_id
                order.save(update_fields=['payment_reference'])

                logger.info(f'Tap payment session created: {charge_id} for order {order.id}')
                return payment_url

            else:
                logger.error(f'Tap API error: {result}')
                raise ValueError(f'Payment error: {result.get("message", "Unknown error")}')

        except requests.RequestException as e:
            logger.error(f'Tap API request failed: {e}')
            raise ValueError(f'Payment service unavailable: {str(e)}')

    def _create_transaction(
        self,
        order: Order,
        transaction_id: str,
        amount: Decimal
    ):
        """إنشاء معاملة مالية"""
        from apps.finance.models import Transaction

        Transaction.objects.create(
            order=order,
            amount=amount,
            transaction_type='payment',
            status='completed',
            payment_gateway='tap',
            gateway_transaction_id=transaction_id,
        )

    def _process_refund(
        self,
        order: Order,
        amount: Decimal,
        user
    ):
        """
        معالجة الاسترداد

        يدعم:
        - استرداد كامل أو جزئي
        - وضع الاختبار
        - Tap Payment Refund API
        """
        import requests
        import logging
        import uuid

        logger = logging.getLogger(__name__)

        # إنشاء سجل الاسترداد
        refund = OrderRefund.objects.create(
            order=order,
            amount=amount,
            status='pending',
            reason=CancellationReason.CUSTOMER_REQUEST,
            requested_by=user,
        )

        tap_config = getattr(settings, 'TAP_PAYMENT_CONFIG', {})
        test_mode = tap_config.get('TEST_MODE', settings.DEBUG)

        # وضع الاختبار
        if test_mode:
            refund_id = f'test_refund_{uuid.uuid4().hex[:8]}'
            refund.status = 'approved'
            refund.transaction_id = refund_id
            refund.processed_at = timezone.now()
            refund.save()

            # تحديث حالة الطلب
            order.payment_status = PaymentStatus.REFUNDED
            order.save(update_fields=['payment_status'])

            logger.info(f'[REFUND TEST] Order {order.id} refunded: {amount} SAR')
            print(f'╔══════════════════════════════════════════╗')
            print(f'║ 💰 REFUND TEST MODE                      ║')
            print(f'║ Order: {str(order.id)[:30]:<30} ║')
            print(f'║ Amount: {amount:<30} SAR ║')
            print(f'║ Refund ID: {refund_id:<27} ║')
            print(f'╚══════════════════════════════════════════╝')
            return refund

        # الإنتاج - Tap Refund API
        api_key = tap_config.get('SECRET_KEY')
        charge_id = order.payment_reference

        if not api_key:
            logger.error('TAP_PAYMENT_CONFIG.SECRET_KEY not configured')
            refund.status = 'failed'
            refund.error_message = 'Payment gateway not configured'
            refund.save()
            return refund

        if not charge_id:
            logger.error(f'No charge_id for order {order.id}')
            refund.status = 'failed'
            refund.error_message = 'No payment reference found'
            refund.save()
            return refund

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }

        payload = {
            'charge_id': charge_id,
            'amount': float(amount),
            'currency': 'SAR',
            'reason': f'إلغاء طلب {order.order_number or order.id}',
            'metadata': {
                'order_id': str(order.id),
                'refund_id': str(refund.id),
            },
        }

        try:
            response = requests.post(
                'https://api.tap.company/v2/refunds',
                json=payload,
                headers=headers,
                timeout=30,
            )

            result = response.json()

            if response.status_code == 200 and result.get('status') in ['CAPTURED', 'pending']:
                refund.status = 'approved'
                refund.transaction_id = result.get('id', '')
                refund.processed_at = timezone.now()
                refund.save()

                # تحديث حالة الطلب
                if amount >= order.paid_amount:
                    order.payment_status = PaymentStatus.REFUNDED
                else:
                    order.payment_status = PaymentStatus.PARTIALLY_REFUNDED
                order.save(update_fields=['payment_status'])

                logger.info(f'Tap refund successful: {result.get("id")} for order {order.id}')

            else:
                refund.status = 'failed'
                refund.error_message = result.get('message', 'Refund failed')
                refund.save()
                logger.error(f'Tap refund failed: {result}')

        except requests.RequestException as e:
            refund.status = 'failed'
            refund.error_message = str(e)
            refund.save()
            logger.error(f'Tap refund request failed: {e}')

        return refund

    def _send_order_notifications(self, order: Order, event: str):
        """
        إرسال إشعارات الطلب

        يرسل إشعارات للعميل والتاجر حسب الحدث
        """
        import asyncio
        import logging

        logger = logging.getLogger(__name__)

        # قوالب الإشعارات
        notification_templates = {
            'confirmed': {
                'customer': {
                    'title': 'تم تأكيد طلبك ✅',
                    'body': f'تم تأكيد طلبك رقم {order.order_number or order.id}. سيتم تجهيزه قريباً.',
                },
                'vendor': {
                    'title': 'طلب جديد 🛒',
                    'body': f'لديك طلب جديد رقم {order.order_number or order.id} بقيمة {order.total_amount} ر.س',
                },
            },
            'accepted': {
                'customer': {
                    'title': 'تم قبول طلبك 👍',
                    'body': f'قام التاجر بقبول طلبك رقم {order.order_number or order.id}. جاري التجهيز.',
                },
            },
            'processing': {
                'customer': {
                    'title': 'جاري تجهيز طلبك 📦',
                    'body': f'طلبك رقم {order.order_number or order.id} قيد التجهيز.',
                },
            },
            'ready': {
                'customer': {
                    'title': 'طلبك جاهز للتسليم 📦',
                    'body': f'طلبك رقم {order.order_number or order.id} جاهز وسيتم تسليمه قريباً.',
                },
            },
            'shipped': {
                'customer': {
                    'title': 'طلبك في الطريق 🚚',
                    'body': f'طلبك رقم {order.order_number or order.id} في الطريق إليك.',
                },
            },
            'out_for_delivery': {
                'customer': {
                    'title': 'السائق في الطريق إليك 🚗',
                    'body': f'السائق في طريقه لتسليم طلبك رقم {order.order_number or order.id}.',
                },
            },
            'delivered': {
                'customer': {
                    'title': 'تم تسليم طلبك ✅',
                    'body': f'تم تسليم طلبك رقم {order.order_number or order.id} بنجاح. شكراً لك!',
                },
                'vendor': {
                    'title': 'تم تسليم الطلب ✅',
                    'body': f'تم تسليم الطلب رقم {order.order_number or order.id} للعميل بنجاح.',
                },
            },
            'cancelled': {
                'customer': {
                    'title': 'تم إلغاء طلبك ❌',
                    'body': f'تم إلغاء طلبك رقم {order.order_number or order.id}. إذا تم الدفع سيتم إرجاع المبلغ.',
                },
                'vendor': {
                    'title': 'تم إلغاء الطلب ❌',
                    'body': f'تم إلغاء الطلب رقم {order.order_number or order.id}.',
                },
            },
        }

        templates = notification_templates.get(event, {})
        if not templates:
            logger.warning(f'No notification template for event: {event}')
            return

        # إرسال الإشعارات
        try:
            from apps.notifications.services import NotificationPayload, get_notification_service
            from apps.notifications.models import DeliveryChannel, NotificationCategory

            notification_service = get_notification_service()

            # إشعار للعميل
            if 'customer' in templates:
                customer_notification = templates['customer']

                async def send_customer_notification():
                    payload = NotificationPayload(
                        recipient_id=order.customer_id,
                        title=customer_notification['title'],
                        body=customer_notification['body'],
                        category=NotificationCategory.ORDER,
                        channels=[
                            DeliveryChannel.WEBSOCKET,
                            DeliveryChannel.PUSH,
                        ],
                        data={
                            'order_id': str(order.id),
                            'event': event,
                            'order_number': order.order_number or str(order.id),
                        },
                        action_url=f'/orders/{order.id}',
                    )
                    await notification_service.send(payload)

                # تشغيل async من sync context
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(send_customer_notification())
                    else:
                        loop.run_until_complete(send_customer_notification())
                except RuntimeError:
                    asyncio.run(send_customer_notification())

            # إشعار للتاجر
            if 'vendor' in templates:
                vendor_notification = templates['vendor']
                vendor_user_id = getattr(order.vendor, 'owner_id', None)

                if vendor_user_id:
                    async def send_vendor_notification():
                        payload = NotificationPayload(
                            recipient_id=vendor_user_id,
                            title=vendor_notification['title'],
                            body=vendor_notification['body'],
                            category=NotificationCategory.ORDER,
                            channels=[
                                DeliveryChannel.WEBSOCKET,
                                DeliveryChannel.PUSH,
                            ],
                            data={
                                'order_id': str(order.id),
                                'event': event,
                            },
                            action_url=f'/vendor/orders/{order.id}',
                        )
                        await notification_service.send(payload)

                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(send_vendor_notification())
                        else:
                            loop.run_until_complete(send_vendor_notification())
                    except RuntimeError:
                        asyncio.run(send_vendor_notification())

            logger.info(f'Order notifications sent for order {order.id}, event: {event}')

        except ImportError as e:
            logger.warning(f'Notifications module not available: {e}')
        except Exception as e:
            logger.error(f'Failed to send order notifications: {e}')

    def _get_valid_transitions(self, current_status: str) -> List[str]:
        """الحصول على التحويلات الصالحة للحالة"""
        transitions = {
            OrderStatus.DRAFT: [OrderStatus.PENDING_PAYMENT, OrderStatus.CANCELLED],
            OrderStatus.PENDING_PAYMENT: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED, OrderStatus.FAILED],
            OrderStatus.CONFIRMED: [OrderStatus.ACCEPTED, OrderStatus.CANCELLED],
            OrderStatus.ACCEPTED: [OrderStatus.PROCESSING, OrderStatus.CANCELLED],
            OrderStatus.PROCESSING: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
            OrderStatus.PREPARING: [OrderStatus.READY],
            OrderStatus.READY: [OrderStatus.SHIPPED, OrderStatus.OUT_FOR_DELIVERY],
            OrderStatus.SHIPPED: [OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED],
            OrderStatus.OUT_FOR_DELIVERY: [OrderStatus.DELIVERED, OrderStatus.FAILED],
            OrderStatus.DELIVERED: [OrderStatus.COMPLETED],
            OrderStatus.COMPLETED: [],
            OrderStatus.CANCELLED: [],
        }
        return transitions.get(current_status, [])


# =============================================
# خدمة التوصيل
# =============================================

class DeliveryService:
    """خدمة إدارة التوصيل"""

    def assign_driver(
        self,
        delivery: OrderDelivery,
        driver,
        admin_user=None
    ) -> bool:
        """تعيين سائق للتوصيل"""
        delivery.driver = driver
        delivery.status = OrderDelivery.DeliveryStatus.ASSIGNED
        delivery.assigned_at = timezone.now()
        delivery.save()

        # تحديث حالة السائق
        if hasattr(driver, 'driver_profile'):
            driver.driver_profile.current_order = delivery.order_id
            driver.driver_profile.is_available = False
            driver.driver_profile.save()

        # إرسال إشعار للسائق
        # TODO: إرسال إشعار

        return True

    def update_location(
        self,
        delivery: OrderDelivery,
        latitude: float,
        longitude: float,
        accuracy: float = None,
        speed: float = None,
        heading: float = None
    ):
        """تحديث موقع التوصيل"""
        from django.contrib.gis.geos import Point
        from .models import DeliveryTrackingPoint

        location = Point(longitude, latitude, srid=4326)

        # تحديث الموقع الحالي
        delivery.current_location = location
        delivery.last_location_update = timezone.now()
        delivery.save(update_fields=['current_location', 'last_location_update'])

        # تسجيل نقطة التتبع
        DeliveryTrackingPoint.objects.create(
            delivery=delivery,
            location=location,
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            speed=speed,
            heading=heading,
        )

    def mark_picked_up(self, delivery: OrderDelivery, driver) -> bool:
        """تسجيل استلام الطلب"""
        delivery.status = OrderDelivery.DeliveryStatus.PICKED_UP
        delivery.picked_up_at = timezone.now()
        delivery.save()

        # تحديث حالة الطلب
        delivery.order.update_status(OrderStatus.OUT_FOR_DELIVERY, driver, 'السائق استلم الطلب')

        return True

    def mark_delivered(
        self,
        delivery: OrderDelivery,
        driver,
        recipient_name: str = '',
        photo=None,
        signature=None,
        notes: str = ''
    ) -> bool:
        """تسجيل تسليم الطلب"""
        delivery.status = OrderDelivery.DeliveryStatus.DELIVERED
        delivery.delivered_at = timezone.now()
        delivery.recipient_name = recipient_name
        delivery.delivery_notes = notes

        if photo:
            delivery.delivery_photo = photo
        if signature:
            delivery.signature = signature

        delivery.save()

        # تحديث حالة الطلب
        delivery.order.update_status(OrderStatus.DELIVERED, driver, 'تم تسليم الطلب')

        # تحرير السائق
        if hasattr(driver, 'driver_profile'):
            driver.driver_profile.current_order = None
            driver.driver_profile.is_available = True
            driver.driver_profile.total_deliveries += 1
            driver.driver_profile.save()

        return True

    def mark_failed(
        self,
        delivery: OrderDelivery,
        driver,
        reason: str
    ) -> bool:
        """تسجيل فشل التوصيل"""
        delivery.attempts += 1
        delivery.last_attempt_at = timezone.now()
        delivery.failure_reason = reason

        if delivery.attempts >= delivery.max_attempts:
            delivery.status = OrderDelivery.DeliveryStatus.FAILED
            delivery.order.update_status(OrderStatus.FAILED, driver, f'فشل التوصيل: {reason}')
        else:
            # جدولة محاولة أخرى
            pass

        delivery.save()

        return True

    def get_nearby_orders(
        self,
        driver,
        latitude: float,
        longitude: float,
        radius_km: float = 10
    ) -> List[OrderDelivery]:
        """الحصول على الطلبات القريبة"""
        from django.contrib.gis.geos import Point
        from django.contrib.gis.measure import D

        location = Point(longitude, latitude, srid=4326)

        return OrderDelivery.objects.filter(
            status=OrderDelivery.DeliveryStatus.PENDING,
            order__status=OrderStatus.READY,
            order__vendor__location__distance_lte=(location, D(km=radius_km))
        ).select_related('order', 'order__vendor', 'order__delivery_address')


# =============================================
# Singletons
# =============================================

order_service = OrderService()
delivery_service = DeliveryService()
