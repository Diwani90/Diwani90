"""
API المتاجر
===========

Django Ninja API للمتاجر والبائعين
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db.models import Q, Avg, Count
from django.shortcuts import get_object_or_404
from ninja import Router, Query, File, UploadedFile, Form
from ninja.pagination import paginate, LimitOffsetPagination

from .models import (
    Store,
    StoreDocument,
    StoreReview,
    StoreServiceArea,
    StoreType,
    StoreStatus,
    VerificationStatus,
)
from .schemas import (
    StoreSchema,
    StoreDetailSchema,
    StoreCreateSchema,
    StoreUpdateSchema,
    StoreListSchema,
    StoreFilterSchema,
    StoreReviewSchema,
    StoreReviewCreateSchema,
    StoreDocumentSchema,
    StoreStatsSchema,
    NearbyStoreSchema,
    MessageSchema,
)
from apps.products.schemas import ProductListSchema

router = Router()


# =============================================
# المتاجر العامة
# =============================================

@router.get('/stores', response=List[StoreListSchema], tags=['المتاجر'])
@paginate(LimitOffsetPagination)
def list_stores(request, filters: StoreFilterSchema = Query(...)):
    """قائمة المتاجر"""
    queryset = Store.objects.filter(status=StoreStatus.ACTIVE)

    # البحث
    if filters.search:
        queryset = queryset.filter(
            Q(name__icontains=filters.search) |
            Q(name_en__icontains=filters.search) |
            Q(description__icontains=filters.search)
        )

    # فلتر النوع
    if filters.store_type:
        queryset = queryset.filter(store_type=filters.store_type)

    # فلتر المدينة
    if filters.city:
        queryset = queryset.filter(city__icontains=filters.city)

    # فلتر التقييم
    if filters.min_rating is not None:
        queryset = queryset.filter(rating__gte=filters.min_rating)

    # فلتر التوصيل المجاني
    if filters.free_delivery:
        queryset = queryset.filter(offers_free_delivery=True)

    # فلتر الموثقين فقط
    if filters.verified_only:
        queryset = queryset.filter(verification_status=VerificationStatus.VERIFIED)

    # فلتر المفتوحين الآن (يحتاج معالجة خاصة)
    # if filters.open_now:
    #     queryset = [s for s in queryset if s.is_open]

    # الترتيب
    order_mapping = {
        'newest': '-created_at',
        'rating': '-rating',
        'popular': '-orders_count',
        'nearest': 'distance',  # يحتاج حساب المسافة
    }
    order_by = order_mapping.get(filters.sort_by, '-rating')
    if order_by != 'distance':
        queryset = queryset.order_by(order_by)

    return queryset


@router.get('/stores/featured', response=List[StoreListSchema], tags=['المتاجر'])
def featured_stores(request, limit: int = 10):
    """المتاجر المميزة"""
    return Store.objects.filter(
        status=StoreStatus.ACTIVE,
        is_featured=True
    ).order_by('-rating')[:limit]


@router.get('/stores/top-rated', response=List[StoreListSchema], tags=['المتاجر'])
def top_rated_stores(request, limit: int = 10):
    """المتاجر الأعلى تقييماً"""
    return Store.objects.filter(
        status=StoreStatus.ACTIVE,
        reviews_count__gte=5  # على الأقل 5 تقييمات
    ).order_by('-rating')[:limit]


@router.get('/stores/nearby', response=List[NearbyStoreSchema], tags=['المتاجر'])
def nearby_stores(
    request,
    latitude: float,
    longitude: float,
    radius_km: int = 20,
    store_type: Optional[str] = None,
    limit: int = 20,
):
    """المتاجر القريبة"""
    user_location = Point(longitude, latitude, srid=4326)

    queryset = Store.objects.filter(
        status=StoreStatus.ACTIVE,
        location__isnull=False,
        location__distance_lte=(user_location, D(km=radius_km))
    ).annotate(
        distance=models.functions.Distance('location', user_location)
    )

    if store_type:
        queryset = queryset.filter(store_type=store_type)

    stores = queryset.order_by('distance')[:limit]

    return [
        {
            **StoreListSchema.from_orm(store).dict(),
            'distance_km': round(store.distance.km, 2) if store.distance else None
        }
        for store in stores
    ]


@router.get('/stores/{store_id}', response=StoreDetailSchema, tags=['المتاجر'])
def get_store(request, store_id: UUID):
    """تفاصيل متجر"""
    store = get_object_or_404(
        Store.objects.prefetch_related('service_areas'),
        id=store_id,
        status=StoreStatus.ACTIVE
    )
    return store


@router.get('/stores/{store_id}/products', response=List[ProductListSchema], tags=['المتاجر'])
@paginate(LimitOffsetPagination)
def store_products(
    request,
    store_id: UUID,
    category_id: Optional[UUID] = None,
    product_type: Optional[str] = None,
):
    """منتجات متجر"""
    from apps.products.models import Product, ProductStatus

    queryset = Product.objects.filter(
        vendor_id=store_id,
        status=ProductStatus.ACTIVE
    )

    if category_id:
        queryset = queryset.filter(category_id=category_id)

    if product_type:
        queryset = queryset.filter(product_type=product_type)

    return queryset.select_related('category').order_by('-created_at')


@router.get('/stores/by-slug/{slug}', response=StoreDetailSchema, tags=['المتاجر'])
def get_store_by_slug(request, slug: str):
    """تفاصيل متجر بالـ slug"""
    return get_object_or_404(Store, slug=slug, status=StoreStatus.ACTIVE)


# =============================================
# تقييمات المتاجر
# =============================================

@router.get('/stores/{store_id}/reviews', response=List[StoreReviewSchema], tags=['تقييمات المتاجر'])
@paginate(LimitOffsetPagination)
def store_reviews(
    request,
    store_id: UUID,
    rating: Optional[int] = None,
):
    """تقييمات متجر"""
    queryset = StoreReview.objects.filter(
        store_id=store_id,
        is_approved=True
    ).select_related('user')

    if rating:
        queryset = queryset.filter(rating=rating)

    return queryset.order_by('-created_at')


@router.post('/stores/{store_id}/reviews', response=StoreReviewSchema, tags=['تقييمات المتاجر'])
def create_store_review(request, store_id: UUID, data: StoreReviewCreateSchema):
    """إضافة تقييم لمتجر"""
    store = get_object_or_404(Store, id=store_id)

    # التحقق من عدم وجود تقييم سابق بدون طلب
    if StoreReview.objects.filter(
        store=store,
        user=request.user,
        order__isnull=True
    ).exists():
        return {'error': 'لقد قمت بتقييم هذا المتجر مسبقاً'}

    review = StoreReview.objects.create(
        store=store,
        user=request.user,
        rating=data.rating,
        title=data.title,
        comment=data.comment,
        delivery_rating=data.delivery_rating,
        quality_rating=data.quality_rating,
        service_rating=data.service_rating,
    )

    return review


# =============================================
# إدارة المتجر (للتاجر)
# =============================================

@router.get('/vendor/store', response=StoreSchema, tags=['متجري'])
def my_store(request):
    """متجري"""
    store = Store.objects.filter(owner=request.user).first()
    if not store:
        return {'error': 'لا يوجد متجر مسجل'}
    return store


@router.post('/vendor/store', response=StoreSchema, tags=['متجري'])
def create_store(request, data: StoreCreateSchema):
    """إنشاء متجر جديد"""
    # التحقق من عدم وجود متجر سابق
    if Store.objects.filter(owner=request.user).exists():
        return {'error': 'لديك متجر مسجل مسبقاً'}

    # إنشاء الموقع الجغرافي
    location = None
    if data.latitude and data.longitude:
        location = Point(data.longitude, data.latitude, srid=4326)

    store = Store.objects.create(
        owner=request.user,
        store_type=data.store_type,
        name=data.name,
        name_en=data.name_en,
        short_description=data.short_description,
        description=data.description,
        phone=data.phone,
        whatsapp=data.whatsapp,
        email=data.email,
        address=data.address,
        city=data.city,
        district=data.district,
        location=location,
        cr_number=data.cr_number,
        vat_number=data.vat_number,
        min_order_amount=data.min_order_amount or 0,
        delivery_radius_km=data.delivery_radius_km or 50,
        offers_free_delivery=data.offers_free_delivery,
        free_delivery_threshold=data.free_delivery_threshold,
        status=StoreStatus.PENDING,
    )

    return store


@router.put('/vendor/store', response=StoreSchema, tags=['متجري'])
def update_store(request, data: StoreUpdateSchema):
    """تحديث متجري"""
    store = get_object_or_404(Store, owner=request.user)

    # تحديث الموقع إن وجد
    if data.latitude and data.longitude:
        store.location = Point(data.longitude, data.latitude, srid=4326)

    for field, value in data.dict(exclude_unset=True, exclude={'latitude', 'longitude'}).items():
        setattr(store, field, value)

    store.save()
    return store


@router.post('/vendor/store/logo', response=MessageSchema, tags=['متجري'])
def upload_logo(request, logo: UploadedFile = File(...)):
    """رفع شعار المتجر"""
    store = get_object_or_404(Store, owner=request.user)
    store.logo = logo
    store.save()
    return {'message': 'تم رفع الشعار بنجاح'}


@router.post('/vendor/store/cover', response=MessageSchema, tags=['متجري'])
def upload_cover(request, cover: UploadedFile = File(...)):
    """رفع صورة الغلاف"""
    store = get_object_or_404(Store, owner=request.user)
    store.cover_image = cover
    store.save()
    return {'message': 'تم رفع صورة الغلاف بنجاح'}


@router.get('/vendor/store/stats', response=StoreStatsSchema, tags=['متجري'])
def store_stats(request):
    """إحصائيات متجري"""
    store = get_object_or_404(Store, owner=request.user)

    from apps.products.models import Product, ProductStatus
    from apps.orders.models import Order
    from django.db.models import Sum
    from django.utils import timezone
    from datetime import timedelta

    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    last_30_days = today - timedelta(days=30)

    # إحصائيات المنتجات
    products_stats = Product.objects.filter(vendor=store).aggregate(
        total=Count('id'),
        active=Count('id', filter=Q(status=ProductStatus.ACTIVE)),
        out_of_stock=Count('id', filter=Q(status=ProductStatus.OUT_OF_STOCK)),
    )

    # إحصائيات الطلبات
    orders_stats = {
        'total': store.orders_count,
        'this_month': 0,  # Order.objects.filter(vendor=store, created_at__gte=this_month_start).count(),
        'pending': 0,
    }

    # إحصائيات المبيعات
    sales_stats = {
        'total': float(store.total_sales),
        'this_month': 0,
        'last_30_days': 0,
    }

    return {
        'store_id': store.id,
        'rating': float(store.rating),
        'reviews_count': store.reviews_count,
        'products': products_stats,
        'orders': orders_stats,
        'sales': sales_stats,
        'verification_status': store.verification_status,
    }


# =============================================
# المستندات والتوثيق
# =============================================

@router.get('/vendor/store/documents', response=List[StoreDocumentSchema], tags=['التوثيق'])
def list_documents(request):
    """قائمة مستندات المتجر"""
    store = get_object_or_404(Store, owner=request.user)
    return store.documents.all()


@router.post('/vendor/store/documents', response=StoreDocumentSchema, tags=['التوثيق'])
def upload_document(
    request,
    document_type: str = Form(...),
    name: str = Form(...),
    file: UploadedFile = File(...),
    expires_at: Optional[str] = Form(None),
):
    """رفع مستند للتوثيق"""
    store = get_object_or_404(Store, owner=request.user)

    doc = StoreDocument.objects.create(
        store=store,
        document_type=document_type,
        name=name,
        file=file,
        expires_at=expires_at,
    )

    return doc


@router.post('/vendor/store/request-verification', response=MessageSchema, tags=['التوثيق'])
def request_verification(request):
    """طلب التوثيق"""
    store = get_object_or_404(Store, owner=request.user)

    # التحقق من اكتمال المستندات
    required_docs = ['cr', 'vat', 'id', 'bank']
    uploaded_types = store.documents.values_list('document_type', flat=True)

    missing = [d for d in required_docs if d not in uploaded_types]
    if missing:
        return {'error': f'المستندات الناقصة: {", ".join(missing)}'}

    store.verification_status = VerificationStatus.PENDING
    store.save()

    return {'message': 'تم إرسال طلب التوثيق بنجاح'}


# =============================================
# مناطق الخدمة
# =============================================

@router.get('/vendor/store/service-areas', tags=['مناطق الخدمة'])
def list_service_areas(request):
    """قائمة مناطق الخدمة"""
    store = get_object_or_404(Store, owner=request.user)
    return store.service_areas.filter(is_active=True)


@router.post('/vendor/store/service-areas', response=MessageSchema, tags=['مناطق الخدمة'])
def add_service_area(
    request,
    name: str,
    city: str,
    districts: List[str],
    delivery_fee: float = 0,
    min_order: float = 0,
):
    """إضافة منطقة خدمة"""
    store = get_object_or_404(Store, owner=request.user)

    StoreServiceArea.objects.create(
        store=store,
        name=name,
        city=city,
        districts=districts,
        delivery_fee=Decimal(str(delivery_fee)),
        min_order=Decimal(str(min_order)),
    )

    return {'message': 'تم إضافة منطقة الخدمة بنجاح'}


# =============================================
# Tap Connect - ربط الحساب البنكي
# =============================================

@router.post('/vendor/store/connect-tap', response=MessageSchema, tags=['المدفوعات'])
def connect_tap_account(
    request,
    bank_name: str,
    iban: str,
    account_name: str,
):
    """ربط حساب Tap للمدفوعات"""
    store = get_object_or_404(Store, owner=request.user)

    # التحقق من التوثيق
    if store.verification_status != VerificationStatus.VERIFIED:
        return {'error': 'يجب توثيق المتجر أولاً'}

    # إنشاء Connected Account في Tap
    from apps.finance.integrations import tap_client

    try:
        result = tap_client.create_connected_account(
            name=store.name,
            email=store.email or request.user.email,
            phone=store.phone,
            iban=iban,
            bank_name=bank_name,
            business_type='company' if store.cr_number else 'individual',
            cr_number=store.cr_number,
            vat_number=store.vat_number,
            metadata={'store_id': str(store.id)}
        )

        store.tap_account_id = result['tap_account_id']
        store.tap_account_status = 'active'
        store.bank_name = bank_name
        store.bank_iban = iban
        store.bank_account_name = account_name
        store.save()

        return {'message': 'تم ربط الحساب بنجاح'}

    except Exception as e:
        return {'error': f'فشل ربط الحساب: {str(e)}'}


@router.get('/vendor/store/balance', tags=['المدفوعات'])
def get_store_balance(request):
    """رصيد المتجر"""
    store = get_object_or_404(Store, owner=request.user)

    from apps.finance.models import VendorBalance

    balance = VendorBalance.objects.filter(vendor=store).first()

    if not balance:
        return {
            'available_balance': 0,
            'pending_balance': 0,
            'total_earned': 0,
            'total_withdrawn': 0,
        }

    return {
        'available_balance': float(balance.available_balance),
        'pending_balance': float(balance.pending_balance),
        'total_earned': float(balance.total_earned),
        'total_withdrawn': float(balance.total_withdrawn),
        'last_synced_at': balance.last_synced_at,
    }
