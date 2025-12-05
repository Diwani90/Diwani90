"""
===================================
منصة ديواني - Orders API
Django Ninja API Endpoints for Cart & Orders
===================================
"""

from typing import List, Optional
from uuid import UUID
from math import ceil
from decimal import Decimal

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.conf import settings

from ninja import Router, Query

from apps.stores.models import Store
from apps.products.models import Product, ProductVariant, ProductAddon
from apps.accounts.models import Address
from .models import (
    Cart, CartItem, CartItemAddon,
    Order, OrderItem, OrderItemAddon, OrderStatusHistory, Coupon
)
from .schemas import (
    CartOutSchema,
    CartItemCreateSchema,
    CartItemUpdateSchema,
    CartItemOutSchema,
    CouponApplySchema,
    CouponValidationSchema,
    CouponOutSchema,
    OrderCreateSchema,
    OrderOutSchema,
    OrderListSchema,
    OrderStatusUpdateSchema,
    OrderCancelSchema,
    OrderStatusHistoryOutSchema,
    CheckoutSummarySchema,
    PaginatedOrderSchema,
    MessageSchema,
    ErrorSchema,
)

# Create router
router = Router(tags=['السلة والطلبات'])


# ===================================
# Cart Endpoints
# ===================================
@router.get('/cart', response=List[CartOutSchema])
def get_user_carts(request):
    """
    سلاتي
    ---
    جميع سلات التسوق الخاصة بك (قد تكون لديك سلة لكل متجر)
    """
    carts = Cart.objects.filter(user=request.user).prefetch_related('items__product', 'items__variant')
    return carts


@router.get('/cart/{store_id}', response={200: CartOutSchema, 404: ErrorSchema})
def get_cart(request, store_id: UUID):
    """
    سلة المتجر
    ---
    الحصول على سلة التسوق لمتجر معين
    """
    try:
        cart = Cart.objects.prefetch_related(
            'items__product', 'items__variant', 'items__addons__addon'
        ).get(user=request.user, store_id=store_id)
        return 200, cart
    except Cart.DoesNotExist:
        return 404, ErrorSchema(message='السلة فارغة')


@router.post('/cart/items', response={201: CartOutSchema, 400: ErrorSchema})
def add_to_cart(request, data: CartItemCreateSchema):
    """
    إضافة للسلة
    ---
    إضافة منتج إلى السلة
    """
    try:
        # Get product
        product = Product.objects.select_related('store').get(
            id=data.product_id,
            status='active',
            is_active=True
        )

        # Validate variant if provided
        variant = None
        if data.variant_id:
            variant = ProductVariant.objects.get(id=data.variant_id, product=product, is_active=True)

        # Check stock
        if product.track_inventory:
            available = variant.stock_quantity if variant else product.stock_quantity
            if data.quantity > available:
                return 400, ErrorSchema(message='الكمية المطلوبة غير متوفرة')

        # Get or create cart
        cart, _ = Cart.objects.get_or_create(
            user=request.user,
            store=product.store
        )

        # Check if item already exists
        existing_item = cart.items.filter(product=product, variant=variant).first()

        if existing_item:
            existing_item.quantity += data.quantity
            existing_item.notes = data.notes or existing_item.notes
            existing_item.save()
            cart_item = existing_item
        else:
            cart_item = CartItem.objects.create(
                cart=cart,
                product=product,
                variant=variant,
                quantity=data.quantity,
                notes=data.notes
            )

        # Add addons
        if data.addons:
            for addon_data in data.addons:
                addon = ProductAddon.objects.get(id=addon_data.addon_id, product=product)
                CartItemAddon.objects.create(
                    cart_item=cart_item,
                    addon=addon,
                    quantity=addon_data.quantity
                )

        cart.refresh_from_db()
        return 201, cart

    except Product.DoesNotExist:
        return 400, ErrorSchema(message='المنتج غير موجود أو غير متاح')
    except ProductVariant.DoesNotExist:
        return 400, ErrorSchema(message='خيار المنتج غير متاح')
    except ProductAddon.DoesNotExist:
        return 400, ErrorSchema(message='الإضافة غير متاحة')
    except Exception as e:
        return 400, ErrorSchema(message=str(e))


@router.patch('/cart/items/{item_id}', response={200: CartOutSchema, 400: ErrorSchema})
def update_cart_item(request, item_id: UUID, data: CartItemUpdateSchema):
    """
    تحديث عنصر السلة
    ---
    تحديث كمية أو ملاحظات عنصر في السلة
    """
    try:
        cart_item = CartItem.objects.select_related('cart', 'product').get(
            id=item_id,
            cart__user=request.user
        )

        if data.quantity is not None:
            # Check stock
            if cart_item.product.track_inventory:
                available = cart_item.variant.stock_quantity if cart_item.variant else cart_item.product.stock_quantity
                if data.quantity > available:
                    return 400, ErrorSchema(message='الكمية المطلوبة غير متوفرة')
            cart_item.quantity = data.quantity

        if data.notes is not None:
            cart_item.notes = data.notes

        cart_item.save()
        cart_item.cart.refresh_from_db()
        return 200, cart_item.cart

    except CartItem.DoesNotExist:
        return 400, ErrorSchema(message='العنصر غير موجود')


@router.delete('/cart/items/{item_id}', response={200: MessageSchema, 404: ErrorSchema})
def remove_from_cart(request, item_id: UUID):
    """
    إزالة من السلة
    ---
    إزالة عنصر من السلة
    """
    try:
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
        cart = cart_item.cart
        cart_item.delete()

        # Delete cart if empty
        if cart.items.count() == 0:
            cart.delete()

        return 200, MessageSchema(message='تم إزالة العنصر من السلة')
    except CartItem.DoesNotExist:
        return 404, ErrorSchema(message='العنصر غير موجود')


@router.delete('/cart/{store_id}', response=MessageSchema)
def clear_cart(request, store_id: UUID):
    """
    تفريغ السلة
    ---
    حذف جميع عناصر السلة
    """
    Cart.objects.filter(user=request.user, store_id=store_id).delete()
    return MessageSchema(message='تم تفريغ السلة')


# ===================================
# Coupon Endpoints
# ===================================
@router.post('/cart/{store_id}/coupon', response={200: CouponValidationSchema, 400: ErrorSchema})
def apply_coupon(request, store_id: UUID, data: CouponApplySchema):
    """
    تطبيق كوبون
    ---
    التحقق من كوبون الخصم وتطبيقه
    """
    try:
        cart = Cart.objects.get(user=request.user, store_id=store_id)

        coupon = Coupon.objects.get(
            Q(code__iexact=data.code),
            Q(store_id=store_id) | Q(store__isnull=True)
        )

        if not coupon.is_valid:
            return 200, CouponValidationSchema(
                is_valid=False,
                coupon=None,
                discount_amount=Decimal('0'),
                message='الكوبون منتهي الصلاحية أو تم استخدامه'
            )

        if cart.subtotal < coupon.min_order_amount:
            return 200, CouponValidationSchema(
                is_valid=False,
                coupon=CouponOutSchema.from_orm(coupon),
                discount_amount=Decimal('0'),
                message=f'الحد الأدنى للطلب {coupon.min_order_amount} ريال'
            )

        discount = coupon.calculate_discount(cart.subtotal)

        return 200, CouponValidationSchema(
            is_valid=True,
            coupon=CouponOutSchema.from_orm(coupon),
            discount_amount=discount,
            message='تم تطبيق الكوبون بنجاح'
        )

    except Cart.DoesNotExist:
        return 400, ErrorSchema(message='السلة فارغة')
    except Coupon.DoesNotExist:
        return 200, CouponValidationSchema(
            is_valid=False,
            coupon=None,
            discount_amount=Decimal('0'),
            message='الكوبون غير صالح'
        )


# ===================================
# Checkout Endpoints
# ===================================
@router.get('/cart/{store_id}/checkout-summary', response={200: dict, 400: ErrorSchema})
def get_checkout_summary(
    request,
    store_id: UUID,
    delivery_address_id: Optional[UUID] = None,
    coupon_code: Optional[str] = None,
    tip_amount: Decimal = Decimal('0')
):
    """
    ملخص الدفع
    ---
    الحصول على ملخص الطلب قبل الدفع
    """
    try:
        cart = Cart.objects.select_related('store').prefetch_related('items').get(
            user=request.user,
            store_id=store_id
        )

        if not cart.items.exists():
            return 400, ErrorSchema(message='السلة فارغة')

        subtotal = cart.subtotal
        delivery_fee = cart.delivery_fee

        # Calculate tax
        tax_rate = settings.DIWANI_SETTINGS.get('TAX_RATE', Decimal('15'))
        tax_amount = subtotal * (tax_rate / 100)

        # Apply coupon if provided
        discount_amount = Decimal('0')
        coupon = None
        if coupon_code:
            try:
                coupon = Coupon.objects.get(
                    Q(code__iexact=coupon_code),
                    Q(store_id=store_id) | Q(store__isnull=True)
                )
                if coupon.is_valid and subtotal >= coupon.min_order_amount:
                    discount_amount = coupon.calculate_discount(subtotal)
            except Coupon.DoesNotExist:
                pass

        total = subtotal + delivery_fee + tax_amount + tip_amount - discount_amount

        # Payment methods
        payment_methods = [
            {'id': 'cash', 'name': 'الدفع عند الاستلام', 'icon': 'cash'},
            {'id': 'card', 'name': 'بطاقة ائتمان', 'icon': 'credit-card'},
            {'id': 'mada', 'name': 'مدى', 'icon': 'mada'},
            {'id': 'apple_pay', 'name': 'Apple Pay', 'icon': 'apple'},
        ]

        # Check wallet balance
        if request.user.wallet_balance >= total:
            payment_methods.append({'id': 'wallet', 'name': f'المحفظة ({request.user.wallet_balance} ر.س)', 'icon': 'wallet'})

        return 200, {
            'subtotal': float(subtotal),
            'delivery_fee': float(delivery_fee),
            'tax_amount': float(tax_amount),
            'discount_amount': float(discount_amount),
            'tip_amount': float(tip_amount),
            'total': float(total),
            'items_count': cart.items_count,
            'store_name': cart.store.name,
            'min_order_met': subtotal >= cart.store.min_order_amount,
            'coupon': CouponOutSchema.from_orm(coupon) if coupon else None,
            'payment_methods': payment_methods,
            'estimated_delivery_time': cart.store.estimated_delivery_time
        }

    except Cart.DoesNotExist:
        return 400, ErrorSchema(message='السلة فارغة')


@router.post('/orders', response={201: OrderOutSchema, 400: ErrorSchema})
def create_order(request, data: OrderCreateSchema):
    """
    إنشاء طلب
    ---
    تأكيد الطلب وإنشائه
    """
    try:
        with transaction.atomic():
            # Get cart
            cart = Cart.objects.select_related('store').prefetch_related(
                'items__product', 'items__variant', 'items__addons__addon'
            ).get(id=data.cart_id, user=request.user)

            if not cart.items.exists():
                return 400, ErrorSchema(message='السلة فارغة')

            store = cart.store

            # Validate minimum order
            if cart.subtotal < store.min_order_amount:
                return 400, ErrorSchema(
                    message=f'الحد الأدنى للطلب {store.min_order_amount} ريال'
                )

            # Get delivery address if delivery
            delivery_address = None
            delivery_address_text = ''
            delivery_location = None

            if data.delivery_type == 'delivery':
                if not data.delivery_address_id:
                    return 400, ErrorSchema(message='يرجى تحديد عنوان التوصيل')

                delivery_address = Address.objects.get(
                    id=data.delivery_address_id,
                    user=request.user
                )
                delivery_address_text = delivery_address.full_address
                delivery_location = delivery_address.location

            # Calculate totals
            subtotal = cart.subtotal
            delivery_fee = cart.delivery_fee if data.delivery_type == 'delivery' else Decimal('0')

            # Tax
            tax_rate = settings.DIWANI_SETTINGS.get('TAX_RATE', Decimal('15'))
            tax_amount = subtotal * (tax_rate / 100)

            # Apply coupon
            discount_amount = Decimal('0')
            coupon = None
            if data.coupon_code:
                try:
                    coupon = Coupon.objects.get(
                        Q(code__iexact=data.coupon_code),
                        Q(store_id=store.id) | Q(store__isnull=True)
                    )
                    if coupon.is_valid and subtotal >= coupon.min_order_amount:
                        discount_amount = coupon.calculate_discount(subtotal)
                        coupon.use()
                except Coupon.DoesNotExist:
                    pass

            # Calculate total
            total = subtotal + delivery_fee + tax_amount + data.tip_amount - discount_amount

            # Validate payment method
            if data.payment_method == 'wallet':
                if request.user.wallet_balance < total:
                    return 400, ErrorSchema(message='رصيد المحفظة غير كافي')

            # Create order
            order = Order.objects.create(
                customer=request.user,
                store=store,
                delivery_type=data.delivery_type,
                delivery_address=delivery_address,
                delivery_address_text=delivery_address_text,
                delivery_location=delivery_location,
                payment_method=data.payment_method,
                subtotal=subtotal,
                delivery_fee=delivery_fee,
                tax_amount=tax_amount,
                discount_amount=discount_amount,
                tip_amount=data.tip_amount,
                total=total,
                coupon=coupon,
                customer_notes=data.customer_notes,
                estimated_preparation_time=store.estimated_delivery_time,
                estimated_delivery_time=30 if data.delivery_type == 'delivery' else None
            )

            # Create order items
            for cart_item in cart.items.all():
                order_item = OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    variant=cart_item.variant,
                    product_name=cart_item.product.name,
                    product_name_en=cart_item.product.name_en,
                    variant_name=cart_item.variant.name if cart_item.variant else '',
                    quantity=cart_item.quantity,
                    unit_price=cart_item.unit_price,
                    notes=cart_item.notes
                )

                # Add addons
                addons_total = Decimal('0')
                for cart_addon in cart_item.addons.all():
                    OrderItemAddon.objects.create(
                        order_item=order_item,
                        addon_name=cart_addon.addon.name,
                        addon_name_en=cart_addon.addon.name_en,
                        quantity=cart_addon.quantity,
                        price=cart_addon.price
                    )
                    addons_total += cart_addon.price * cart_addon.quantity

                order_item.addons_total = addons_total
                order_item.save(update_fields=['addons_total'])

                # Decrease stock
                if cart_item.product.track_inventory:
                    cart_item.product.decrease_stock(cart_item.quantity)

            # Process wallet payment
            if data.payment_method == 'wallet':
                request.user.deduct_from_wallet(total, f'طلب #{order.order_number}')
                order.payment_status = Order.PaymentStatus.PAID
                order.save(update_fields=['payment_status'])

            # Create status history
            OrderStatusHistory.objects.create(
                order=order,
                status=order.status,
                notes='تم إنشاء الطلب',
                changed_by=request.user
            )

            # Delete cart
            cart.delete()

            return 201, order

    except Cart.DoesNotExist:
        return 400, ErrorSchema(message='السلة غير موجودة')
    except Address.DoesNotExist:
        return 400, ErrorSchema(message='العنوان غير موجود')
    except Exception as e:
        return 400, ErrorSchema(message=str(e))


# ===================================
# Order Listing Endpoints
# ===================================
@router.get('/orders', response=PaginatedOrderSchema)
def list_orders(
    request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    status: Optional[str] = None
):
    """
    طلباتي
    ---
    قائمة طلباتك
    """
    queryset = Order.objects.filter(customer=request.user).select_related('store')

    if status:
        queryset = queryset.filter(status=status)

    queryset = queryset.order_by('-placed_at')

    total = queryset.count()
    pages = ceil(total / page_size)
    offset = (page - 1) * page_size
    items = list(queryset[offset:offset + page_size])

    return PaginatedOrderSchema(
        items=[OrderListSchema.from_orm(o) for o in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get('/orders/active', response=List[OrderListSchema])
def list_active_orders(request):
    """
    الطلبات النشطة
    ---
    الطلبات الجارية حالياً
    """
    active_statuses = ['pending', 'confirmed', 'preparing', 'ready', 'picked_up', 'on_the_way']
    return Order.objects.filter(
        customer=request.user,
        status__in=active_statuses
    ).select_related('store').order_by('-placed_at')


@router.get('/orders/{order_id}', response={200: OrderOutSchema, 404: ErrorSchema})
def get_order(request, order_id: UUID):
    """
    تفاصيل الطلب
    """
    try:
        order = Order.objects.select_related(
            'store', 'customer', 'driver', 'coupon'
        ).prefetch_related(
            'items__addons'
        ).get(id=order_id, customer=request.user)
        return 200, order
    except Order.DoesNotExist:
        return 404, ErrorSchema(message='الطلب غير موجود')


@router.get('/orders/number/{order_number}', response={200: OrderOutSchema, 404: ErrorSchema})
def get_order_by_number(request, order_number: str):
    """
    تفاصيل الطلب برقم الطلب
    """
    try:
        order = Order.objects.select_related(
            'store', 'customer', 'driver', 'coupon'
        ).prefetch_related(
            'items__addons'
        ).get(order_number=order_number, customer=request.user)
        return 200, order
    except Order.DoesNotExist:
        return 404, ErrorSchema(message='الطلب غير موجود')


@router.get('/orders/{order_id}/history', response=List[OrderStatusHistoryOutSchema])
def get_order_history(request, order_id: UUID):
    """
    سجل حالات الطلب
    """
    return OrderStatusHistory.objects.filter(
        order_id=order_id,
        order__customer=request.user
    ).select_related('changed_by')


@router.post('/orders/{order_id}/cancel', response={200: OrderOutSchema, 400: ErrorSchema})
def cancel_order(request, order_id: UUID, data: OrderCancelSchema):
    """
    إلغاء الطلب
    """
    try:
        order = Order.objects.get(id=order_id, customer=request.user)

        # Check if order can be cancelled
        if order.status not in ['pending', 'confirmed']:
            return 400, ErrorSchema(message='لا يمكن إلغاء الطلب في هذه المرحلة')

        order.cancel(data.reason, request.user)

        # Refund if paid
        if order.payment_status == Order.PaymentStatus.PAID:
            if order.payment_method == 'wallet':
                request.user.add_to_wallet(order.total, f'استرداد طلب #{order.order_number}')
            order.payment_status = Order.PaymentStatus.REFUNDED
            order.save(update_fields=['payment_status'])

        # Restore stock
        for item in order.items.all():
            if item.product and item.product.track_inventory:
                item.product.increase_stock(item.quantity)

        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            status=order.status,
            notes=f'تم إلغاء الطلب: {data.reason}',
            changed_by=request.user
        )

        return 200, order

    except Order.DoesNotExist:
        return 400, ErrorSchema(message='الطلب غير موجود')


# ===================================
# Vendor Order Management
# ===================================
@router.get('/my-stores/{store_id}/orders', response=PaginatedOrderSchema)
def list_store_orders(
    request,
    store_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    status: Optional[str] = None
):
    """
    طلبات المتجر
    ---
    قائمة طلبات متجرك (للتجار)
    """
    queryset = Order.objects.filter(
        store_id=store_id,
        store__owner=request.user
    )

    if status:
        queryset = queryset.filter(status=status)

    queryset = queryset.order_by('-placed_at')

    total = queryset.count()
    pages = ceil(total / page_size)
    offset = (page - 1) * page_size
    items = list(queryset[offset:offset + page_size])

    return PaginatedOrderSchema(
        items=[OrderListSchema.from_orm(o) for o in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get('/my-stores/{store_id}/orders/pending', response=List[OrderOutSchema])
def list_pending_orders(request, store_id: UUID):
    """
    الطلبات الجديدة
    ---
    الطلبات المنتظرة التأكيد
    """
    return Order.objects.filter(
        store_id=store_id,
        store__owner=request.user,
        status='pending'
    ).select_related('customer').prefetch_related('items').order_by('placed_at')


@router.get('/my-stores/{store_id}/orders/{order_id}', response={200: OrderOutSchema, 404: ErrorSchema})
def get_store_order(request, store_id: UUID, order_id: UUID):
    """
    تفاصيل طلب المتجر
    """
    try:
        order = Order.objects.select_related(
            'customer', 'driver'
        ).prefetch_related(
            'items__addons'
        ).get(id=order_id, store_id=store_id, store__owner=request.user)
        return 200, order
    except Order.DoesNotExist:
        return 404, ErrorSchema(message='الطلب غير موجود')


@router.post('/my-stores/{store_id}/orders/{order_id}/status', response={200: OrderOutSchema, 400: ErrorSchema})
def update_order_status(request, store_id: UUID, order_id: UUID, data: OrderStatusUpdateSchema):
    """
    تحديث حالة الطلب
    ---
    تحديث حالة الطلب (للتجار)
    """
    try:
        order = Order.objects.get(id=order_id, store_id=store_id, store__owner=request.user)

        # Validate status transition
        valid_transitions = {
            'pending': ['confirmed', 'cancelled'],
            'confirmed': ['preparing', 'cancelled'],
            'preparing': ['ready', 'cancelled'],
            'ready': ['picked_up'],
            'picked_up': ['on_the_way'],
            'on_the_way': ['delivered'],
        }

        if data.status not in valid_transitions.get(order.status, []):
            return 400, ErrorSchema(message='لا يمكن تغيير الحالة إلى هذه القيمة')

        # Update order status
        order.status = data.status
        timestamp_field = {
            'confirmed': 'confirmed_at',
            'preparing': 'preparing_at',
            'ready': 'ready_at',
            'picked_up': 'picked_up_at',
            'delivered': 'delivered_at',
            'cancelled': 'cancelled_at',
        }.get(data.status)

        if timestamp_field:
            setattr(order, timestamp_field, timezone.now())

        if data.estimated_time:
            order.estimated_preparation_time = data.estimated_time

        order.save()

        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            status=data.status,
            notes=data.notes,
            changed_by=request.user
        )

        # Update store stats if delivered
        if data.status == 'delivered':
            order.complete()

        return 200, order

    except Order.DoesNotExist:
        return 400, ErrorSchema(message='الطلب غير موجود')


@router.get('/my-stores/{store_id}/orders/stats', response=dict)
def get_orders_stats(request, store_id: UUID):
    """
    إحصائيات الطلبات
    """
    from django.db.models import Sum, Count
    from datetime import timedelta

    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    base_query = Order.objects.filter(store_id=store_id, store__owner=request.user)

    # Today's stats
    today_orders = base_query.filter(placed_at__date=today)
    today_revenue = today_orders.filter(status='delivered').aggregate(total=Sum('total'))['total'] or 0

    # Weekly stats
    week_orders = base_query.filter(placed_at__date__gte=week_ago)
    week_revenue = week_orders.filter(status='delivered').aggregate(total=Sum('total'))['total'] or 0

    # Monthly stats
    month_orders = base_query.filter(placed_at__date__gte=month_ago)
    month_revenue = month_orders.filter(status='delivered').aggregate(total=Sum('total'))['total'] or 0

    # Status breakdown
    status_counts = base_query.values('status').annotate(count=Count('id'))

    return {
        'today': {
            'orders': today_orders.count(),
            'revenue': float(today_revenue),
        },
        'week': {
            'orders': week_orders.count(),
            'revenue': float(week_revenue),
        },
        'month': {
            'orders': month_orders.count(),
            'revenue': float(month_revenue),
        },
        'by_status': {item['status']: item['count'] for item in status_counts},
        'pending_count': base_query.filter(status='pending').count(),
    }
