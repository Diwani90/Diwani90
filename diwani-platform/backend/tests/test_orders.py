"""
اختبارات نظام الطلبات
=====================
"""

import pytest
from decimal import Decimal

from django.contrib.gis.geos import Point
from django.utils import timezone

from apps.orders.models import (
    Order, OrderItem, OrderStatus, PaymentStatus,
    PaymentMethod, OrderType
)


# =============================================
# Order Model Tests
# =============================================

@pytest.mark.django_db
class TestOrderModel:
    """اختبارات نموذج الطلب"""

    def test_create_order(self, customer_user, store):
        """اختبار إنشاء طلب"""
        order = Order.objects.create(
            customer=customer_user,
            vendor=store,
            order_type=OrderType.PRODUCT,
            status=OrderStatus.DRAFT,
            subtotal=Decimal('500.00'),
            delivery_fee=Decimal('50.00'),
            tax_amount=Decimal('82.50'),
            total_amount=Decimal('632.50'),
            delivery_address='الرياض، حي النرجس',
            delivery_location=Point(46.6500, 24.7500, srid=4326),
        )

        assert order.id is not None
        assert order.order_number is not None
        assert order.status == OrderStatus.DRAFT

    def test_order_number_format(self, customer_user, store):
        """اختبار تنسيق رقم الطلب"""
        order = Order.objects.create(
            customer=customer_user,
            vendor=store,
            subtotal=Decimal('100.00'),
            total_amount=Decimal('100.00'),
        )

        # رقم الطلب يجب أن يحتوي على التاريخ
        assert order.order_number is not None
        assert len(order.order_number) > 8

    def test_order_tax_calculation(self, customer_user, store):
        """اختبار حساب الضريبة"""
        subtotal = Decimal('1000.00')
        tax_rate = Decimal('0.15')
        expected_tax = subtotal * tax_rate

        order = Order.objects.create(
            customer=customer_user,
            vendor=store,
            subtotal=subtotal,
            tax_amount=expected_tax,
            total_amount=subtotal + expected_tax,
        )

        assert order.tax_amount == Decimal('150.00')
        assert order.total_amount == Decimal('1150.00')


# =============================================
# Order Status Tests
# =============================================

@pytest.mark.django_db
class TestOrderStatus:
    """اختبارات حالة الطلب"""

    def test_order_workflow(self, order):
        """اختبار سير عمل الطلب"""
        # تأكيد الطلب
        order.status = OrderStatus.CONFIRMED
        order.confirmed_at = timezone.now()
        order.save()

        assert order.status == OrderStatus.CONFIRMED

        # قيد التجهيز
        order.status = OrderStatus.PROCESSING
        order.save()

        assert order.status == OrderStatus.PROCESSING

        # جاهز للتوصيل
        order.status = OrderStatus.READY
        order.save()

        # في الطريق
        order.status = OrderStatus.OUT_FOR_DELIVERY
        order.save()

        # تم التسليم
        order.status = OrderStatus.DELIVERED
        order.delivered_at = timezone.now()
        order.save()

        assert order.status == OrderStatus.DELIVERED
        assert order.delivered_at is not None

    def test_order_cancellation(self, order, customer_user):
        """اختبار إلغاء الطلب"""
        order.status = OrderStatus.CANCELLED
        order.cancelled_at = timezone.now()
        order.cancelled_by = customer_user
        order.cancellation_reason = 'تغيير في الخطط'
        order.save()

        assert order.status == OrderStatus.CANCELLED
        assert order.cancellation_reason == 'تغيير في الخطط'


# =============================================
# Order Item Tests
# =============================================

@pytest.mark.django_db
class TestOrderItems:
    """اختبارات عناصر الطلب"""

    def test_add_order_item(self, order, product):
        """اختبار إضافة عنصر للطلب"""
        item = OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            product_sku=product.sku,
            quantity=Decimal('10'),
            unit_price=product.price,
            subtotal=product.price * 10,
        )

        assert item.id is not None
        assert item.subtotal == Decimal('250.00')

    def test_order_items_total(self, order, product):
        """اختبار مجموع العناصر"""
        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            quantity=Decimal('5'),
            unit_price=Decimal('25.00'),
            subtotal=Decimal('125.00'),
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            quantity=Decimal('3'),
            unit_price=Decimal('50.00'),
            subtotal=Decimal('150.00'),
        )

        items_total = sum(
            item.subtotal for item in order.items.all()
        )

        assert items_total == Decimal('275.00')


# =============================================
# Payment Tests
# =============================================

@pytest.mark.django_db
class TestOrderPayment:
    """اختبارات الدفع"""

    def test_payment_status_flow(self, order):
        """اختبار حالة الدفع"""
        # قيد الانتظار
        order.payment_status = PaymentStatus.PENDING
        order.save()

        assert order.payment_status == PaymentStatus.PENDING

        # تم الدفع
        order.payment_status = PaymentStatus.PAID
        order.paid_at = timezone.now()
        order.save()

        assert order.payment_status == PaymentStatus.PAID
        assert order.paid_at is not None

    def test_payment_method(self, order):
        """اختبار طريقة الدفع"""
        order.payment_method = PaymentMethod.CARD
        order.save()

        assert order.payment_method == PaymentMethod.CARD

        order.payment_method = PaymentMethod.MADA
        order.save()

        assert order.payment_method == PaymentMethod.MADA

    def test_refund(self, order):
        """اختبار الاسترداد"""
        order.payment_status = PaymentStatus.PAID
        order.paid_at = timezone.now()
        order.save()

        # استرداد
        order.payment_status = PaymentStatus.REFUNDED
        order.refunded_at = timezone.now()
        order.refund_amount = order.total_amount
        order.save()

        assert order.payment_status == PaymentStatus.REFUNDED
        assert order.refund_amount == order.total_amount


# =============================================
# Order Type Tests
# =============================================

@pytest.mark.django_db
class TestOrderTypes:
    """اختبارات أنواع الطلبات"""

    def test_product_order(self, customer_user, store):
        """اختبار طلب منتجات"""
        order = Order.objects.create(
            customer=customer_user,
            vendor=store,
            order_type=OrderType.PRODUCT,
            subtotal=Decimal('500.00'),
            total_amount=Decimal('575.00'),
        )

        assert order.order_type == OrderType.PRODUCT

    def test_service_order(self, customer_user, store):
        """اختبار طلب خدمة"""
        order = Order.objects.create(
            customer=customer_user,
            vendor=store,
            order_type=OrderType.SERVICE,
            subtotal=Decimal('1000.00'),
            total_amount=Decimal('1150.00'),
        )

        assert order.order_type == OrderType.SERVICE

    def test_rental_order(self, customer_user, store):
        """اختبار طلب تأجير"""
        order = Order.objects.create(
            customer=customer_user,
            vendor=store,
            order_type=OrderType.RENTAL,
            subtotal=Decimal('2000.00'),
            total_amount=Decimal('2300.00'),
        )

        assert order.order_type == OrderType.RENTAL
