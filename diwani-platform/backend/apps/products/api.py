"""
API المنتجات
============

Django Ninja API للمنتجات والأقسام
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from django.db.models import Q, Avg, Count
from django.shortcuts import get_object_or_404
from ninja import Router, Query, File, UploadedFile, Form
from ninja.pagination import paginate, LimitOffsetPagination
from ninja.security import HttpBearer

from .models import (
    Category,
    Product,
    ProductVariant,
    ProductImage,
    ProductSpecification,
    ProductOption,
    ProductOptionValue,
    ProductReview,
    ProductType,
    ProductStatus,
    PricingType,
)
from .schemas import (
    CategorySchema,
    CategoryTreeSchema,
    ProductSchema,
    ProductDetailSchema,
    ProductCreateSchema,
    ProductUpdateSchema,
    ProductListSchema,
    ProductFilterSchema,
    ProductVariantSchema,
    ProductReviewSchema,
    ProductReviewCreateSchema,
    PriceCalculationRequest,
    PriceCalculationResponse,
    MessageSchema,
)

router = Router()


# =============================================
# الأقسام - Categories
# =============================================

@router.get('/categories', response=List[CategorySchema], tags=['الأقسام'])
def list_categories(
    request,
    parent_id: Optional[UUID] = None,
    category_type: Optional[str] = None,
    active_only: bool = True,
):
    """قائمة الأقسام"""
    queryset = Category.objects.all()

    if active_only:
        queryset = queryset.filter(is_active=True)

    if parent_id:
        queryset = queryset.filter(parent_id=parent_id)
    else:
        queryset = queryset.filter(parent__isnull=True)  # الأقسام الرئيسية فقط

    if category_type:
        queryset = queryset.filter(category_type=category_type)

    return queryset.order_by('sort_order', 'name')


@router.get('/categories/tree', response=List[CategoryTreeSchema], tags=['الأقسام'])
def categories_tree(request, category_type: Optional[str] = None):
    """شجرة الأقسام الكاملة"""
    queryset = Category.objects.filter(
        is_active=True,
        parent__isnull=True
    ).prefetch_related('children', 'children__children')

    if category_type:
        queryset = queryset.filter(category_type=category_type)

    return queryset.order_by('sort_order')


@router.get('/categories/{category_id}', response=CategorySchema, tags=['الأقسام'])
def get_category(request, category_id: UUID):
    """تفاصيل قسم"""
    return get_object_or_404(Category, id=category_id, is_active=True)


@router.get('/categories/{category_id}/products', response=List[ProductListSchema], tags=['الأقسام'])
@paginate(LimitOffsetPagination)
def category_products(
    request,
    category_id: UUID,
    include_children: bool = True,
):
    """منتجات قسم معين"""
    category = get_object_or_404(Category, id=category_id)

    if include_children:
        # تضمين الأقسام الفرعية
        category_ids = [category.id] + list(
            category.get_descendants().values_list('id', flat=True)
        )
        queryset = Product.objects.filter(
            category_id__in=category_ids,
            status=ProductStatus.ACTIVE
        )
    else:
        queryset = Product.objects.filter(
            category=category,
            status=ProductStatus.ACTIVE
        )

    return queryset.select_related('vendor', 'category').order_by('-created_at')


# =============================================
# المنتجات - Products
# =============================================

@router.get('/products', response=List[ProductListSchema], tags=['المنتجات'])
@paginate(LimitOffsetPagination)
def list_products(
    request,
    filters: ProductFilterSchema = Query(...),
):
    """قائمة المنتجات مع الفلترة"""
    queryset = Product.objects.filter(status=ProductStatus.ACTIVE)

    # البحث
    if filters.search:
        queryset = queryset.filter(
            Q(name__icontains=filters.search) |
            Q(name_en__icontains=filters.search) |
            Q(description__icontains=filters.search) |
            Q(sku__icontains=filters.search)
        )

    # فلتر القسم
    if filters.category_id:
        queryset = queryset.filter(category_id=filters.category_id)

    # فلتر المتجر
    if filters.vendor_id:
        queryset = queryset.filter(vendor_id=filters.vendor_id)

    # فلتر نوع المنتج
    if filters.product_type:
        queryset = queryset.filter(product_type=filters.product_type)

    # فلتر نوع التسعير
    if filters.pricing_type:
        queryset = queryset.filter(pricing_type=filters.pricing_type)

    # فلتر السعر
    if filters.min_price is not None:
        queryset = queryset.filter(price__gte=filters.min_price)
    if filters.max_price is not None:
        queryset = queryset.filter(price__lte=filters.max_price)

    # فلتر التقييم
    if filters.min_rating is not None:
        queryset = queryset.filter(rating__gte=filters.min_rating)

    # فلتر التوصيل المجاني
    if filters.free_delivery:
        queryset = queryset.filter(free_delivery=True)

    # فلتر المتاح فقط
    if filters.in_stock:
        queryset = queryset.filter(
            Q(track_inventory=False) |
            Q(stock_quantity__gt=0) |
            Q(allow_backorder=True)
        )

    # الترتيب
    order_mapping = {
        'newest': '-created_at',
        'price_low': 'price',
        'price_high': '-price',
        'rating': '-rating',
        'popular': '-orders_count',
    }
    order_by = order_mapping.get(filters.sort_by, '-created_at')
    queryset = queryset.order_by(order_by)

    return queryset.select_related('vendor', 'category')


@router.get('/products/featured', response=List[ProductListSchema], tags=['المنتجات'])
def featured_products(request, limit: int = 10):
    """المنتجات المميزة"""
    return Product.objects.filter(
        status=ProductStatus.ACTIVE,
        is_featured=True
    ).select_related('vendor', 'category')[:limit]


@router.get('/products/new', response=List[ProductListSchema], tags=['المنتجات'])
def new_products(request, limit: int = 10):
    """المنتجات الجديدة"""
    return Product.objects.filter(
        status=ProductStatus.ACTIVE,
        is_new=True
    ).select_related('vendor', 'category').order_by('-created_at')[:limit]


@router.get('/products/{product_id}', response=ProductDetailSchema, tags=['المنتجات'])
def get_product(request, product_id: UUID):
    """تفاصيل منتج"""
    product = get_object_or_404(
        Product.objects.select_related('vendor', 'category')
        .prefetch_related(
            'images',
            'variants',
            'specifications',
            'options__values'
        ),
        id=product_id,
        status=ProductStatus.ACTIVE
    )

    # زيادة عداد المشاهدات
    Product.objects.filter(id=product_id).update(
        views_count=product.views_count + 1
    )

    return product


@router.get('/products/{product_id}/related', response=List[ProductListSchema], tags=['المنتجات'])
def related_products(request, product_id: UUID, limit: int = 6):
    """المنتجات ذات الصلة"""
    product = get_object_or_404(Product, id=product_id)

    return Product.objects.filter(
        category=product.category,
        status=ProductStatus.ACTIVE
    ).exclude(id=product_id).select_related('vendor')[:limit]


@router.post('/products/{product_id}/calculate-price', response=PriceCalculationResponse, tags=['المنتجات'])
def calculate_price(request, product_id: UUID, data: PriceCalculationRequest):
    """حساب السعر بناءً على الكمية والخيارات"""
    product = get_object_or_404(Product, id=product_id)

    from apps.finance.services import pricing_service

    # حساب سعر المنتج
    item_price, item_breakdown = pricing_service.calculate_item_price(
        pricing_type=product.pricing_type,
        base_price=product.price,
        quantity=Decimal(str(data.quantity)),
        context=data.context or {},
        **product.pricing_config
    )

    # إضافة تعديلات الخيارات
    options_adjustment = Decimal('0')
    if data.selected_options:
        for option_id, value_id in data.selected_options.items():
            try:
                option_value = ProductOptionValue.objects.get(
                    id=value_id,
                    option__product=product
                )
                options_adjustment += option_value.price_adjustment
            except ProductOptionValue.DoesNotExist:
                pass

    # المجموع
    subtotal = item_price + (options_adjustment * data.quantity)

    # الضريبة
    tax_rate = Decimal('0.15')  # 15% VAT
    tax_amount = (subtotal * tax_rate).quantize(Decimal('0.01'))

    total = subtotal + tax_amount

    return {
        'product_id': product_id,
        'quantity': data.quantity,
        'unit_price': float(product.price),
        'item_total': float(item_price),
        'options_adjustment': float(options_adjustment * data.quantity),
        'subtotal': float(subtotal),
        'tax_rate': float(tax_rate * 100),
        'tax_amount': float(tax_amount),
        'total': float(total),
        'breakdown': item_breakdown,
        'pricing_type': product.pricing_type,
    }


# =============================================
# تقييمات المنتجات - Reviews
# =============================================

@router.get('/products/{product_id}/reviews', response=List[ProductReviewSchema], tags=['التقييمات'])
@paginate(LimitOffsetPagination)
def product_reviews(
    request,
    product_id: UUID,
    rating: Optional[int] = None,
):
    """تقييمات منتج"""
    queryset = ProductReview.objects.filter(
        product_id=product_id,
        is_approved=True
    ).select_related('user')

    if rating:
        queryset = queryset.filter(rating=rating)

    return queryset.order_by('-created_at')


@router.post('/products/{product_id}/reviews', response=ProductReviewSchema, tags=['التقييمات'])
def create_review(request, product_id: UUID, data: ProductReviewCreateSchema):
    """إضافة تقييم"""
    product = get_object_or_404(Product, id=product_id)

    # التحقق من عدم وجود تقييم سابق
    if ProductReview.objects.filter(
        product=product,
        user=request.user
    ).exists():
        return {'error': 'لقد قمت بتقييم هذا المنتج مسبقاً'}

    review = ProductReview.objects.create(
        product=product,
        user=request.user,
        rating=data.rating,
        title=data.title,
        comment=data.comment,
        is_verified_purchase=False,  # يتم التحقق لاحقاً
    )

    return review


# =============================================
# API للتجار - Vendor Products
# =============================================

@router.get('/vendor/products', response=List[ProductSchema], tags=['منتجات التاجر'])
@paginate(LimitOffsetPagination)
def vendor_products(request, status: Optional[str] = None):
    """منتجات التاجر"""
    queryset = Product.objects.filter(vendor__owner=request.user)

    if status:
        queryset = queryset.filter(status=status)

    return queryset.order_by('-created_at')


@router.post('/vendor/products', response=ProductSchema, tags=['منتجات التاجر'])
def create_product(request, data: ProductCreateSchema):
    """إنشاء منتج جديد"""
    from apps.stores.models import Store

    # التحقق من ملكية المتجر
    store = get_object_or_404(Store, id=data.vendor_id, owner=request.user)

    product = Product.objects.create(
        vendor=store,
        category_id=data.category_id,
        product_type=data.product_type,
        name=data.name,
        name_en=data.name_en,
        short_description=data.short_description,
        description=data.description,
        pricing_type=data.pricing_type,
        price=data.price,
        compare_at_price=data.compare_at_price,
        unit=data.unit,
        min_quantity=data.min_quantity,
        max_quantity=data.max_quantity,
        track_inventory=data.track_inventory,
        stock_quantity=data.stock_quantity,
        lead_time_hours=data.lead_time_hours,
        delivery_option=data.delivery_option,
        free_delivery=data.free_delivery,
        status=ProductStatus.DRAFT,
    )

    return product


@router.put('/vendor/products/{product_id}', response=ProductSchema, tags=['منتجات التاجر'])
def update_product(request, product_id: UUID, data: ProductUpdateSchema):
    """تحديث منتج"""
    product = get_object_or_404(
        Product,
        id=product_id,
        vendor__owner=request.user
    )

    for field, value in data.dict(exclude_unset=True).items():
        setattr(product, field, value)

    product.save()
    return product


@router.delete('/vendor/products/{product_id}', response=MessageSchema, tags=['منتجات التاجر'])
def delete_product(request, product_id: UUID):
    """حذف منتج"""
    product = get_object_or_404(
        Product,
        id=product_id,
        vendor__owner=request.user
    )

    product.status = ProductStatus.DISCONTINUED
    product.save()

    return {'message': 'تم حذف المنتج بنجاح'}


@router.post('/vendor/products/{product_id}/images', response=MessageSchema, tags=['منتجات التاجر'])
def upload_product_image(
    request,
    product_id: UUID,
    image: UploadedFile = File(...),
    is_primary: bool = Form(False),
):
    """رفع صورة منتج"""
    product = get_object_or_404(
        Product,
        id=product_id,
        vendor__owner=request.user
    )

    product_image = ProductImage.objects.create(
        product=product,
        image=image,
        is_primary=is_primary,
    )

    return {'message': 'تم رفع الصورة بنجاح', 'image_id': str(product_image.id)}


@router.post('/vendor/products/{product_id}/publish', response=ProductSchema, tags=['منتجات التاجر'])
def publish_product(request, product_id: UUID):
    """نشر منتج"""
    product = get_object_or_404(
        Product,
        id=product_id,
        vendor__owner=request.user
    )

    # التحقق من اكتمال البيانات
    if not product.images.exists():
        return {'error': 'يجب إضافة صورة واحدة على الأقل'}

    if not product.price or product.price <= 0:
        return {'error': 'يجب تحديد سعر صحيح'}

    product.status = ProductStatus.ACTIVE
    product.save()

    return product
