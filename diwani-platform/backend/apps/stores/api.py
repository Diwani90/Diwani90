"""
===================================
منصة ديواني - Stores API
Django Ninja API Endpoints for Stores
===================================
"""

from typing import List, Optional
from uuid import UUID
from math import ceil

from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.db.models import Q
from django.utils import timezone

from ninja import Router, File, Query
from ninja.files import UploadedFile

from .models import Store, StoreCategory, StoreWorkingHours, StoreGallery, StoreReview, FavoriteStore
from .schemas import (
    StoreCategoryOutSchema,
    StoreCategoryListSchema,
    StoreOutSchema,
    StoreListSchema,
    StoreCreateSchema,
    StoreUpdateSchema,
    WorkingHoursSchema,
    WorkingHoursOutSchema,
    StoreGalleryOutSchema,
    StoreReviewCreateSchema,
    StoreReviewOutSchema,
    StoreReviewResponseSchema,
    FavoriteStoreOutSchema,
    StoreFilterSchema,
    PaginatedStoreSchema,
    MessageSchema,
    ErrorSchema,
)

# Create router
router = Router(tags=['المتاجر'])


# ===================================
# Store Categories Endpoints
# ===================================
@router.get('/categories', response=List[StoreCategoryListSchema])
def list_categories(request):
    """
    قائمة فئات المتاجر
    ---
    جميع فئات المتاجر النشطة
    """
    return StoreCategory.objects.filter(is_active=True, parent__isnull=True)


@router.get('/categories/featured', response=List[StoreCategoryListSchema])
def list_featured_categories(request):
    """
    الفئات المميزة
    ---
    الفئات المميزة للعرض في الصفحة الرئيسية
    """
    return StoreCategory.objects.filter(is_active=True, is_featured=True)


@router.get('/categories/{category_id}', response={200: StoreCategoryOutSchema, 404: ErrorSchema})
def get_category(request, category_id: UUID):
    """
    تفاصيل فئة
    ---
    الحصول على تفاصيل فئة معينة
    """
    try:
        category = StoreCategory.objects.get(id=category_id)
        return 200, category
    except StoreCategory.DoesNotExist:
        return 404, ErrorSchema(message='الفئة غير موجودة')


@router.get('/categories/{category_id}/subcategories', response=List[StoreCategoryListSchema])
def list_subcategories(request, category_id: UUID):
    """
    الفئات الفرعية
    ---
    قائمة الفئات الفرعية لفئة معينة
    """
    return StoreCategory.objects.filter(parent_id=category_id, is_active=True)


# ===================================
# Store Listing Endpoints
# ===================================
@router.get('/stores', response=PaginatedStoreSchema)
def list_stores(
    request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    category_id: Optional[UUID] = None,
    city: Optional[str] = None,
    district: Optional[str] = None,
    store_type: Optional[str] = None,
    is_open: Optional[bool] = None,
    is_featured: Optional[bool] = None,
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    search: Optional[str] = None,
    latitude: Optional[float] = Query(None, ge=-90, le=90),
    longitude: Optional[float] = Query(None, ge=-180, le=180),
    radius_km: Optional[int] = Query(None, ge=1, le=50),
    sort_by: str = '-is_featured,-rating'
):
    """
    قائمة المتاجر
    ---
    تصفح المتاجر مع التصفية والترتيب
    """
    queryset = Store.objects.filter(status='active')

    # Apply filters
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    if city:
        queryset = queryset.filter(city__icontains=city)
    if district:
        queryset = queryset.filter(district__icontains=district)
    if store_type:
        queryset = queryset.filter(store_type=store_type)
    if is_open is not None:
        queryset = queryset.filter(is_open=is_open)
    if is_featured is not None:
        queryset = queryset.filter(is_featured=is_featured)
    if min_rating:
        queryset = queryset.filter(rating__gte=min_rating)

    # Search
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(name_en__icontains=search) |
            Q(description__icontains=search)
        )

    # Location-based filtering
    if latitude and longitude:
        point = Point(longitude, latitude, srid=4326)
        queryset = queryset.annotate(distance=Distance('location', point))

        if radius_km:
            queryset = queryset.filter(location__distance_lte=(point, D(km=radius_km)))

        # Sort by distance if location provided
        sort_by = 'distance'

    # Sorting
    if sort_by:
        sort_fields = sort_by.split(',')
        queryset = queryset.order_by(*sort_fields)

    # Pagination
    total = queryset.count()
    pages = ceil(total / page_size)
    offset = (page - 1) * page_size
    items = list(queryset[offset:offset + page_size])

    return PaginatedStoreSchema(
        items=[StoreListSchema.from_orm(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get('/stores/featured', response=List[StoreListSchema])
def list_featured_stores(request, limit: int = Query(10, ge=1, le=50)):
    """
    المتاجر المميزة
    ---
    قائمة المتاجر المميزة للصفحة الرئيسية
    """
    stores = Store.objects.filter(
        status='active',
        is_featured=True
    ).order_by('-rating')[:limit]
    return stores


@router.get('/stores/nearby', response=List[StoreListSchema])
def list_nearby_stores(
    request,
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: int = Query(10, ge=1, le=50),
    limit: int = Query(20, ge=1, le=50)
):
    """
    المتاجر القريبة
    ---
    المتاجر القريبة من موقعك
    """
    point = Point(longitude, latitude, srid=4326)
    stores = Store.objects.filter(
        status='active',
        location__isnull=False
    ).annotate(
        distance=Distance('location', point)
    ).filter(
        location__distance_lte=(point, D(km=radius_km))
    ).order_by('distance')[:limit]

    return stores


@router.get('/stores/{store_id}', response={200: StoreOutSchema, 404: ErrorSchema})
def get_store(request, store_id: UUID):
    """
    تفاصيل المتجر
    ---
    الحصول على تفاصيل متجر معين
    """
    try:
        store = Store.objects.select_related('category').get(id=store_id, status='active')
        return 200, store
    except Store.DoesNotExist:
        return 404, ErrorSchema(message='المتجر غير موجود')


@router.get('/stores/slug/{slug}', response={200: StoreOutSchema, 404: ErrorSchema})
def get_store_by_slug(request, slug: str):
    """
    تفاصيل المتجر بالمعرف
    ---
    الحصول على تفاصيل متجر بالمعرف النصي
    """
    try:
        store = Store.objects.select_related('category').get(slug=slug, status='active')
        return 200, store
    except Store.DoesNotExist:
        return 404, ErrorSchema(message='المتجر غير موجود')


# ===================================
# Store Working Hours
# ===================================
@router.get('/stores/{store_id}/working-hours', response=List[WorkingHoursOutSchema])
def get_store_working_hours(request, store_id: UUID):
    """
    ساعات العمل
    ---
    ساعات عمل المتجر لجميع أيام الأسبوع
    """
    return StoreWorkingHours.objects.filter(store_id=store_id)


# ===================================
# Store Gallery
# ===================================
@router.get('/stores/{store_id}/gallery', response=List[StoreGalleryOutSchema])
def get_store_gallery(request, store_id: UUID):
    """
    صور المتجر
    ---
    معرض صور المتجر
    """
    return StoreGallery.objects.filter(store_id=store_id)


# ===================================
# Store Reviews
# ===================================
@router.get('/stores/{store_id}/reviews', response=List[StoreReviewOutSchema])
def list_store_reviews(
    request,
    store_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50)
):
    """
    تقييمات المتجر
    ---
    قائمة تقييمات العملاء للمتجر
    """
    offset = (page - 1) * page_size
    reviews = StoreReview.objects.filter(
        store_id=store_id,
        is_visible=True
    ).select_related('user')[offset:offset + page_size]
    return reviews


@router.post('/stores/{store_id}/reviews', response={201: StoreReviewOutSchema, 400: ErrorSchema})
def create_store_review(request, store_id: UUID, data: StoreReviewCreateSchema):
    """
    إضافة تقييم
    ---
    إضافة تقييم جديد للمتجر
    """
    try:
        # Check if user already reviewed this store
        if StoreReview.objects.filter(store_id=store_id, user=request.user).exists():
            return 400, ErrorSchema(message='لقد قمت بتقييم هذا المتجر مسبقاً')

        review = StoreReview.objects.create(
            store_id=store_id,
            user=request.user,
            **data.dict(exclude={'order_id'}),
            order_id=data.order_id if data.order_id else None,
            is_verified=bool(data.order_id)
        )
        return 201, review
    except Exception as e:
        return 400, ErrorSchema(message=str(e))


# ===================================
# Favorite Stores
# ===================================
@router.get('/favorites/stores', response=List[FavoriteStoreOutSchema])
def list_favorite_stores(request):
    """
    المتاجر المفضلة
    ---
    قائمة متاجرك المفضلة
    """
    return FavoriteStore.objects.filter(user=request.user).select_related('store')


@router.post('/stores/{store_id}/favorite', response={201: MessageSchema, 400: ErrorSchema})
def add_to_favorites(request, store_id: UUID):
    """
    إضافة للمفضلة
    ---
    إضافة متجر للمفضلة
    """
    try:
        FavoriteStore.objects.create(user=request.user, store_id=store_id)
        return 201, MessageSchema(message='تمت الإضافة للمفضلة')
    except Exception as e:
        if 'unique' in str(e).lower():
            return 400, ErrorSchema(message='المتجر موجود بالفعل في المفضلة')
        return 400, ErrorSchema(message=str(e))


@router.delete('/stores/{store_id}/favorite', response={200: MessageSchema, 404: ErrorSchema})
def remove_from_favorites(request, store_id: UUID):
    """
    إزالة من المفضلة
    ---
    إزالة متجر من المفضلة
    """
    try:
        favorite = FavoriteStore.objects.get(user=request.user, store_id=store_id)
        favorite.delete()
        return 200, MessageSchema(message='تمت الإزالة من المفضلة')
    except FavoriteStore.DoesNotExist:
        return 404, ErrorSchema(message='المتجر غير موجود في المفضلة')


# ===================================
# Vendor Store Management
# ===================================
@router.get('/my-stores', response=List[StoreOutSchema])
def list_my_stores(request):
    """
    متاجري
    ---
    قائمة المتاجر التي تملكها
    """
    return Store.objects.filter(owner=request.user)


@router.post('/my-stores', response={201: StoreOutSchema, 400: ErrorSchema})
def create_store(request, data: StoreCreateSchema):
    """
    إنشاء متجر جديد
    ---
    إنشاء متجر جديد (للتجار)
    """
    try:
        store_data = data.dict(exclude={'latitude', 'longitude', 'category_id'})

        # Create location point
        if data.latitude and data.longitude:
            store_data['location'] = Point(data.longitude, data.latitude, srid=4326)

        store = Store.objects.create(
            owner=request.user,
            category_id=data.category_id,
            **store_data
        )
        return 201, store
    except Exception as e:
        return 400, ErrorSchema(message=str(e))


@router.patch('/my-stores/{store_id}', response={200: StoreOutSchema, 400: ErrorSchema, 404: ErrorSchema})
def update_store(request, store_id: UUID, data: StoreUpdateSchema):
    """
    تحديث المتجر
    ---
    تحديث بيانات متجرك
    """
    try:
        store = Store.objects.get(id=store_id, owner=request.user)
        update_data = data.dict(exclude_unset=True, exclude={'latitude', 'longitude', 'category_id'})

        # Update location if coordinates provided
        if data.latitude is not None and data.longitude is not None:
            store.location = Point(data.longitude, data.latitude, srid=4326)

        if data.category_id:
            store.category_id = data.category_id

        for field, value in update_data.items():
            setattr(store, field, value)

        store.save()
        return 200, store
    except Store.DoesNotExist:
        return 404, ErrorSchema(message='المتجر غير موجود')
    except Exception as e:
        return 400, ErrorSchema(message=str(e))


@router.post('/my-stores/{store_id}/logo', response={200: StoreOutSchema, 400: ErrorSchema})
def upload_store_logo(request, store_id: UUID, file: UploadedFile = File(...)):
    """
    رفع شعار المتجر
    """
    try:
        store = Store.objects.get(id=store_id, owner=request.user)
        store.logo = file
        store.save(update_fields=['logo'])
        return 200, store
    except Store.DoesNotExist:
        return 400, ErrorSchema(message='المتجر غير موجود')


@router.post('/my-stores/{store_id}/cover', response={200: StoreOutSchema, 400: ErrorSchema})
def upload_store_cover(request, store_id: UUID, file: UploadedFile = File(...)):
    """
    رفع صورة الغلاف
    """
    try:
        store = Store.objects.get(id=store_id, owner=request.user)
        store.cover_image = file
        store.save(update_fields=['cover_image'])
        return 200, store
    except Store.DoesNotExist:
        return 400, ErrorSchema(message='المتجر غير موجود')


@router.post('/my-stores/{store_id}/working-hours', response={200: List[WorkingHoursOutSchema], 400: ErrorSchema})
def set_working_hours(request, store_id: UUID, hours: List[WorkingHoursSchema]):
    """
    تحديث ساعات العمل
    ---
    تحديث ساعات عمل المتجر لجميع الأيام
    """
    try:
        store = Store.objects.get(id=store_id, owner=request.user)

        # Delete existing hours
        StoreWorkingHours.objects.filter(store=store).delete()

        # Create new hours
        created_hours = []
        for hour in hours:
            wh = StoreWorkingHours.objects.create(
                store=store,
                **hour.dict()
            )
            created_hours.append(wh)

        return 200, created_hours
    except Store.DoesNotExist:
        return 400, ErrorSchema(message='المتجر غير موجود')


@router.post('/my-stores/{store_id}/gallery', response={201: StoreGalleryOutSchema, 400: ErrorSchema})
def add_gallery_image(
    request,
    store_id: UUID,
    file: UploadedFile = File(...),
    caption: str = ''
):
    """
    إضافة صورة للمعرض
    """
    try:
        store = Store.objects.get(id=store_id, owner=request.user)
        gallery = StoreGallery.objects.create(
            store=store,
            image=file,
            caption=caption,
            sort_order=store.gallery.count()
        )
        return 201, gallery
    except Store.DoesNotExist:
        return 400, ErrorSchema(message='المتجر غير موجود')


@router.delete('/my-stores/{store_id}/gallery/{image_id}', response={200: MessageSchema, 404: ErrorSchema})
def delete_gallery_image(request, store_id: UUID, image_id: UUID):
    """
    حذف صورة من المعرض
    """
    try:
        gallery = StoreGallery.objects.get(id=image_id, store_id=store_id, store__owner=request.user)
        gallery.delete()
        return 200, MessageSchema(message='تم حذف الصورة')
    except StoreGallery.DoesNotExist:
        return 404, ErrorSchema(message='الصورة غير موجودة')


@router.post('/my-stores/{store_id}/reviews/{review_id}/respond', response={200: StoreReviewOutSchema, 400: ErrorSchema})
def respond_to_review(request, store_id: UUID, review_id: UUID, data: StoreReviewResponseSchema):
    """
    الرد على تقييم
    ---
    رد صاحب المتجر على تقييم عميل
    """
    try:
        review = StoreReview.objects.get(id=review_id, store_id=store_id, store__owner=request.user)
        review.store_response = data.response
        review.responded_at = timezone.now()
        review.save(update_fields=['store_response', 'responded_at'])
        return 200, review
    except StoreReview.DoesNotExist:
        return 400, ErrorSchema(message='التقييم غير موجود')


# ===================================
# Store Statistics (for vendors)
# ===================================
@router.get('/my-stores/{store_id}/stats', response=dict)
def get_store_stats(request, store_id: UUID):
    """
    إحصائيات المتجر
    ---
    إحصائيات وأرقام المتجر
    """
    try:
        store = Store.objects.get(id=store_id, owner=request.user)

        return {
            'total_orders': store.total_orders,
            'total_sales': float(store.total_sales),
            'rating': float(store.rating),
            'rating_count': store.rating_count,
            'products_count': store.products.filter(is_active=True).count(),
            'reviews_count': store.reviews.count(),
            'favorites_count': store.favorited_by.count(),
        }
    except Store.DoesNotExist:
        return {'error': 'المتجر غير موجود'}
