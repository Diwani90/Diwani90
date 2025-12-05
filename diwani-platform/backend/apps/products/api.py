"""
===================================
منصة ديواني - Products API
Django Ninja API Endpoints for Products
===================================
"""

from typing import List, Optional
from uuid import UUID
from math import ceil
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone

from ninja import Router, File, Query
from ninja.files import UploadedFile

from apps.stores.models import Store
from .models import (
    Product, ProductCategory, ProductImage, ProductVariant,
    ProductAddon, ProductAddonGroup, AddonGroupItem,
    ProductReview, FavoriteProduct
)
from .schemas import (
    ProductCategoryOutSchema,
    ProductCategoryListSchema,
    ProductCategoryCreateSchema,
    ProductCategoryUpdateSchema,
    ProductOutSchema,
    ProductListSchema,
    ProductCreateSchema,
    ProductUpdateSchema,
    ProductImageSchema,
    ProductVariantOutSchema,
    ProductVariantCreateSchema,
    ProductVariantUpdateSchema,
    ProductAddonOutSchema,
    ProductAddonCreateSchema,
    ProductAddonGroupOutSchema,
    ProductAddonGroupCreateSchema,
    ProductReviewCreateSchema,
    ProductReviewOutSchema,
    FavoriteProductOutSchema,
    PaginatedProductSchema,
    MessageSchema,
    ErrorSchema,
)

# Create router
router = Router(tags=['المنتجات'])


# ===================================
# Product Categories Endpoints
# ===================================
@router.get('/stores/{store_id}/categories', response=List[ProductCategoryListSchema])
def list_store_categories(request, store_id: UUID):
    """
    فئات منتجات المتجر
    ---
    قائمة فئات المنتجات لمتجر معين
    """
    return ProductCategory.objects.filter(store_id=store_id, is_active=True, parent__isnull=True)


@router.get('/categories/{category_id}', response={200: ProductCategoryOutSchema, 404: ErrorSchema})
def get_category(request, category_id: UUID):
    """
    تفاصيل فئة
    """
    try:
        return 200, ProductCategory.objects.get(id=category_id)
    except ProductCategory.DoesNotExist:
        return 404, ErrorSchema(message='الفئة غير موجودة')


# ===================================
# Product Listing Endpoints
# ===================================
@router.get('/stores/{store_id}/products', response=PaginatedProductSchema)
def list_store_products(
    request,
    store_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    category_id: Optional[UUID] = None,
    search: Optional[str] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    is_featured: Optional[bool] = None,
    in_stock: Optional[bool] = None,
    sort_by: str = '-is_featured,-created_at'
):
    """
    منتجات المتجر
    ---
    قائمة منتجات متجر معين مع التصفية
    """
    queryset = Product.objects.filter(store_id=store_id, status='active', is_active=True)

    # Apply filters
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(name_en__icontains=search) |
            Q(description__icontains=search) |
            Q(sku__icontains=search)
        )
    if min_price is not None:
        queryset = queryset.filter(price__gte=min_price)
    if max_price is not None:
        queryset = queryset.filter(price__lte=max_price)
    if is_featured is not None:
        queryset = queryset.filter(is_featured=is_featured)
    if in_stock is not None:
        if in_stock:
            queryset = queryset.filter(
                Q(track_inventory=False) | Q(stock_quantity__gt=0)
            )
        else:
            queryset = queryset.filter(track_inventory=True, stock_quantity=0)

    # Sorting
    if sort_by:
        sort_fields = sort_by.split(',')
        queryset = queryset.order_by(*sort_fields)

    # Pagination
    total = queryset.count()
    pages = ceil(total / page_size)
    offset = (page - 1) * page_size
    items = list(queryset.select_related('store', 'category')[offset:offset + page_size])

    return PaginatedProductSchema(
        items=[ProductListSchema.from_orm(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get('/products', response=PaginatedProductSchema)
def search_products(
    request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    search: Optional[str] = None,
    city: Optional[str] = None,
    store_category_id: Optional[UUID] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    sort_by: str = '-is_featured,-rating'
):
    """
    بحث المنتجات
    ---
    البحث في جميع المنتجات عبر المتاجر
    """
    queryset = Product.objects.filter(
        status='active',
        is_active=True,
        store__status='active'
    )

    # Apply filters
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(name_en__icontains=search) |
            Q(description__icontains=search)
        )
    if city:
        queryset = queryset.filter(store__city__icontains=city)
    if store_category_id:
        queryset = queryset.filter(store__category_id=store_category_id)
    if min_price is not None:
        queryset = queryset.filter(price__gte=min_price)
    if max_price is not None:
        queryset = queryset.filter(price__lte=max_price)

    # Sorting
    if sort_by:
        sort_fields = sort_by.split(',')
        queryset = queryset.order_by(*sort_fields)

    # Pagination
    total = queryset.count()
    pages = ceil(total / page_size)
    offset = (page - 1) * page_size
    items = list(queryset.select_related('store', 'category')[offset:offset + page_size])

    return PaginatedProductSchema(
        items=[ProductListSchema.from_orm(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get('/products/featured', response=List[ProductListSchema])
def list_featured_products(request, limit: int = Query(20, ge=1, le=50)):
    """
    المنتجات المميزة
    ---
    قائمة المنتجات المميزة للصفحة الرئيسية
    """
    products = Product.objects.filter(
        status='active',
        is_active=True,
        is_featured=True,
        store__status='active'
    ).select_related('store', 'category').order_by('-rating')[:limit]
    return products


@router.get('/products/{product_id}', response={200: ProductOutSchema, 404: ErrorSchema})
def get_product(request, product_id: UUID):
    """
    تفاصيل المنتج
    ---
    الحصول على تفاصيل منتج معين
    """
    try:
        product = Product.objects.select_related(
            'store', 'category'
        ).prefetch_related(
            'images', 'variants', 'addons', 'addon_groups__items'
        ).get(id=product_id)

        # Increment view count
        product.view_count += 1
        product.save(update_fields=['view_count'])

        return 200, product
    except Product.DoesNotExist:
        return 404, ErrorSchema(message='المنتج غير موجود')


@router.get('/products/slug/{store_slug}/{product_slug}', response={200: ProductOutSchema, 404: ErrorSchema})
def get_product_by_slug(request, store_slug: str, product_slug: str):
    """
    تفاصيل المنتج بالمعرف
    """
    try:
        product = Product.objects.select_related(
            'store', 'category'
        ).prefetch_related(
            'images', 'variants', 'addons', 'addon_groups__items'
        ).get(store__slug=store_slug, slug=product_slug)

        product.view_count += 1
        product.save(update_fields=['view_count'])

        return 200, product
    except Product.DoesNotExist:
        return 404, ErrorSchema(message='المنتج غير موجود')


# ===================================
# Product Reviews
# ===================================
@router.get('/products/{product_id}/reviews', response=List[ProductReviewOutSchema])
def list_product_reviews(
    request,
    product_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50)
):
    """
    تقييمات المنتج
    """
    offset = (page - 1) * page_size
    reviews = ProductReview.objects.filter(
        product_id=product_id,
        is_visible=True
    ).select_related('user')[offset:offset + page_size]
    return reviews


@router.post('/products/{product_id}/reviews', response={201: ProductReviewOutSchema, 400: ErrorSchema})
def create_product_review(request, product_id: UUID, data: ProductReviewCreateSchema):
    """
    إضافة تقييم للمنتج
    """
    try:
        if ProductReview.objects.filter(product_id=product_id, user=request.user).exists():
            return 400, ErrorSchema(message='لقد قمت بتقييم هذا المنتج مسبقاً')

        review = ProductReview.objects.create(
            product_id=product_id,
            user=request.user,
            **data.dict()
        )
        return 201, review
    except Exception as e:
        return 400, ErrorSchema(message=str(e))


# ===================================
# Favorite Products
# ===================================
@router.get('/favorites/products', response=List[FavoriteProductOutSchema])
def list_favorite_products(request):
    """
    المنتجات المفضلة
    """
    return FavoriteProduct.objects.filter(user=request.user).select_related('product__store')


@router.post('/products/{product_id}/favorite', response={201: MessageSchema, 400: ErrorSchema})
def add_product_to_favorites(request, product_id: UUID):
    """
    إضافة منتج للمفضلة
    """
    try:
        FavoriteProduct.objects.create(user=request.user, product_id=product_id)
        return 201, MessageSchema(message='تمت الإضافة للمفضلة')
    except Exception as e:
        if 'unique' in str(e).lower():
            return 400, ErrorSchema(message='المنتج موجود بالفعل في المفضلة')
        return 400, ErrorSchema(message=str(e))


@router.delete('/products/{product_id}/favorite', response={200: MessageSchema, 404: ErrorSchema})
def remove_product_from_favorites(request, product_id: UUID):
    """
    إزالة منتج من المفضلة
    """
    try:
        favorite = FavoriteProduct.objects.get(user=request.user, product_id=product_id)
        favorite.delete()
        return 200, MessageSchema(message='تمت الإزالة من المفضلة')
    except FavoriteProduct.DoesNotExist:
        return 404, ErrorSchema(message='المنتج غير موجود في المفضلة')


# ===================================
# Vendor Product Management
# ===================================
@router.get('/my-stores/{store_id}/products', response=PaginatedProductSchema)
def list_my_products(
    request,
    store_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    status: Optional[str] = None,
    category_id: Optional[UUID] = None,
    search: Optional[str] = None
):
    """
    منتجاتي
    ---
    قائمة منتجاتك (للتجار)
    """
    queryset = Product.objects.filter(store_id=store_id, store__owner=request.user)

    if status:
        queryset = queryset.filter(status=status)
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) | Q(sku__icontains=search)
        )

    total = queryset.count()
    pages = ceil(total / page_size)
    offset = (page - 1) * page_size
    items = list(queryset[offset:offset + page_size])

    return PaginatedProductSchema(
        items=[ProductListSchema.from_orm(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.post('/my-stores/{store_id}/products', response={201: ProductOutSchema, 400: ErrorSchema})
def create_product(request, store_id: UUID, data: ProductCreateSchema):
    """
    إضافة منتج جديد
    """
    try:
        store = Store.objects.get(id=store_id, owner=request.user)
        product_data = data.dict(exclude={'category_id'})

        product = Product.objects.create(
            store=store,
            category_id=data.category_id,
            **product_data
        )
        return 201, product
    except Store.DoesNotExist:
        return 400, ErrorSchema(message='المتجر غير موجود')
    except Exception as e:
        return 400, ErrorSchema(message=str(e))


@router.get('/my-stores/{store_id}/products/{product_id}', response={200: ProductOutSchema, 404: ErrorSchema})
def get_my_product(request, store_id: UUID, product_id: UUID):
    """
    تفاصيل منتجي
    """
    try:
        product = Product.objects.get(id=product_id, store_id=store_id, store__owner=request.user)
        return 200, product
    except Product.DoesNotExist:
        return 404, ErrorSchema(message='المنتج غير موجود')


@router.patch('/my-stores/{store_id}/products/{product_id}', response={200: ProductOutSchema, 400: ErrorSchema})
def update_product(request, store_id: UUID, product_id: UUID, data: ProductUpdateSchema):
    """
    تحديث المنتج
    """
    try:
        product = Product.objects.get(id=product_id, store_id=store_id, store__owner=request.user)
        update_data = data.dict(exclude_unset=True, exclude={'category_id'})

        if data.category_id:
            product.category_id = data.category_id

        for field, value in update_data.items():
            setattr(product, field, value)

        product.save()
        return 200, product
    except Product.DoesNotExist:
        return 400, ErrorSchema(message='المنتج غير موجود')
    except Exception as e:
        return 400, ErrorSchema(message=str(e))


@router.delete('/my-stores/{store_id}/products/{product_id}', response={200: MessageSchema, 404: ErrorSchema})
def delete_product(request, store_id: UUID, product_id: UUID):
    """
    حذف المنتج
    """
    try:
        product = Product.objects.get(id=product_id, store_id=store_id, store__owner=request.user)
        product.delete()
        return 200, MessageSchema(message='تم حذف المنتج')
    except Product.DoesNotExist:
        return 404, ErrorSchema(message='المنتج غير موجود')


@router.post('/my-stores/{store_id}/products/{product_id}/image', response={200: ProductOutSchema, 400: ErrorSchema})
def upload_product_image(request, store_id: UUID, product_id: UUID, file: UploadedFile = File(...)):
    """
    رفع صورة المنتج الرئيسية
    """
    try:
        product = Product.objects.get(id=product_id, store_id=store_id, store__owner=request.user)
        product.image = file
        product.save(update_fields=['image'])
        return 200, product
    except Product.DoesNotExist:
        return 400, ErrorSchema(message='المنتج غير موجود')


@router.post('/my-stores/{store_id}/products/{product_id}/images', response={201: ProductImageSchema, 400: ErrorSchema})
def add_product_image(
    request,
    store_id: UUID,
    product_id: UUID,
    file: UploadedFile = File(...),
    alt_text: str = ''
):
    """
    إضافة صورة إضافية للمنتج
    """
    try:
        product = Product.objects.get(id=product_id, store_id=store_id, store__owner=request.user)
        image = ProductImage.objects.create(
            product=product,
            image=file,
            alt_text=alt_text,
            sort_order=product.images.count()
        )
        return 201, image
    except Product.DoesNotExist:
        return 400, ErrorSchema(message='المنتج غير موجود')


@router.delete('/my-stores/{store_id}/products/{product_id}/images/{image_id}', response={200: MessageSchema, 404: ErrorSchema})
def delete_product_image(request, store_id: UUID, product_id: UUID, image_id: UUID):
    """
    حذف صورة المنتج
    """
    try:
        image = ProductImage.objects.get(id=image_id, product_id=product_id, product__store_id=store_id)
        image.delete()
        return 200, MessageSchema(message='تم حذف الصورة')
    except ProductImage.DoesNotExist:
        return 404, ErrorSchema(message='الصورة غير موجودة')


# ===================================
# Product Variants Management
# ===================================
@router.post('/my-stores/{store_id}/products/{product_id}/variants', response={201: ProductVariantOutSchema, 400: ErrorSchema})
def create_product_variant(request, store_id: UUID, product_id: UUID, data: ProductVariantCreateSchema):
    """
    إضافة خيار للمنتج
    """
    try:
        product = Product.objects.get(id=product_id, store_id=store_id, store__owner=request.user)
        variant = ProductVariant.objects.create(
            product=product,
            **data.dict(),
            sort_order=product.variants.count()
        )
        return 201, variant
    except Product.DoesNotExist:
        return 400, ErrorSchema(message='المنتج غير موجود')


@router.patch('/my-stores/{store_id}/products/{product_id}/variants/{variant_id}', response={200: ProductVariantOutSchema, 400: ErrorSchema})
def update_product_variant(request, store_id: UUID, product_id: UUID, variant_id: UUID, data: ProductVariantUpdateSchema):
    """
    تحديث خيار المنتج
    """
    try:
        variant = ProductVariant.objects.get(id=variant_id, product_id=product_id, product__store_id=store_id)
        update_data = data.dict(exclude_unset=True)

        for field, value in update_data.items():
            setattr(variant, field, value)

        variant.save()
        return 200, variant
    except ProductVariant.DoesNotExist:
        return 400, ErrorSchema(message='الخيار غير موجود')


@router.delete('/my-stores/{store_id}/products/{product_id}/variants/{variant_id}', response={200: MessageSchema, 404: ErrorSchema})
def delete_product_variant(request, store_id: UUID, product_id: UUID, variant_id: UUID):
    """
    حذف خيار المنتج
    """
    try:
        variant = ProductVariant.objects.get(id=variant_id, product_id=product_id, product__store_id=store_id)
        variant.delete()
        return 200, MessageSchema(message='تم حذف الخيار')
    except ProductVariant.DoesNotExist:
        return 404, ErrorSchema(message='الخيار غير موجود')


# ===================================
# Product Addons Management
# ===================================
@router.post('/my-stores/{store_id}/products/{product_id}/addons', response={201: ProductAddonOutSchema, 400: ErrorSchema})
def create_product_addon(request, store_id: UUID, product_id: UUID, data: ProductAddonCreateSchema):
    """
    إضافة إضافة للمنتج
    """
    try:
        product = Product.objects.get(id=product_id, store_id=store_id, store__owner=request.user)
        addon = ProductAddon.objects.create(
            product=product,
            **data.dict(),
            sort_order=product.addons.count()
        )
        return 201, addon
    except Product.DoesNotExist:
        return 400, ErrorSchema(message='المنتج غير موجود')


@router.delete('/my-stores/{store_id}/products/{product_id}/addons/{addon_id}', response={200: MessageSchema, 404: ErrorSchema})
def delete_product_addon(request, store_id: UUID, product_id: UUID, addon_id: UUID):
    """
    حذف إضافة المنتج
    """
    try:
        addon = ProductAddon.objects.get(id=addon_id, product_id=product_id, product__store_id=store_id)
        addon.delete()
        return 200, MessageSchema(message='تم حذف الإضافة')
    except ProductAddon.DoesNotExist:
        return 404, ErrorSchema(message='الإضافة غير موجودة')


# ===================================
# Product Categories Management
# ===================================
@router.post('/my-stores/{store_id}/categories', response={201: ProductCategoryOutSchema, 400: ErrorSchema})
def create_product_category(request, store_id: UUID, data: ProductCategoryCreateSchema):
    """
    إضافة فئة منتجات جديدة
    """
    try:
        store = Store.objects.get(id=store_id, owner=request.user)
        category = ProductCategory.objects.create(
            store=store,
            **data.dict(exclude={'parent_id'}),
            parent_id=data.parent_id
        )
        return 201, category
    except Store.DoesNotExist:
        return 400, ErrorSchema(message='المتجر غير موجود')


@router.patch('/my-stores/{store_id}/categories/{category_id}', response={200: ProductCategoryOutSchema, 400: ErrorSchema})
def update_product_category(request, store_id: UUID, category_id: UUID, data: ProductCategoryUpdateSchema):
    """
    تحديث فئة المنتجات
    """
    try:
        category = ProductCategory.objects.get(id=category_id, store_id=store_id, store__owner=request.user)
        update_data = data.dict(exclude_unset=True)

        for field, value in update_data.items():
            setattr(category, field, value)

        category.save()
        return 200, category
    except ProductCategory.DoesNotExist:
        return 400, ErrorSchema(message='الفئة غير موجودة')


@router.delete('/my-stores/{store_id}/categories/{category_id}', response={200: MessageSchema, 404: ErrorSchema})
def delete_product_category(request, store_id: UUID, category_id: UUID):
    """
    حذف فئة المنتجات
    """
    try:
        category = ProductCategory.objects.get(id=category_id, store_id=store_id, store__owner=request.user)

        # Check if category has products
        if category.products.exists():
            return 400, ErrorSchema(message='لا يمكن حذف فئة تحتوي على منتجات')

        category.delete()
        return 200, MessageSchema(message='تم حذف الفئة')
    except ProductCategory.DoesNotExist:
        return 404, ErrorSchema(message='الفئة غير موجودة')


@router.post('/my-stores/{store_id}/categories/{category_id}/image', response={200: ProductCategoryOutSchema, 400: ErrorSchema})
def upload_category_image(request, store_id: UUID, category_id: UUID, file: UploadedFile = File(...)):
    """
    رفع صورة الفئة
    """
    try:
        category = ProductCategory.objects.get(id=category_id, store_id=store_id, store__owner=request.user)
        category.image = file
        category.save(update_fields=['image'])
        return 200, category
    except ProductCategory.DoesNotExist:
        return 400, ErrorSchema(message='الفئة غير موجودة')


# ===================================
# Stock Management
# ===================================
@router.post('/my-stores/{store_id}/products/{product_id}/stock', response={200: ProductOutSchema, 400: ErrorSchema})
def update_product_stock(request, store_id: UUID, product_id: UUID, quantity: int):
    """
    تحديث المخزون
    """
    try:
        product = Product.objects.get(id=product_id, store_id=store_id, store__owner=request.user)
        product.stock_quantity = quantity
        product.save(update_fields=['stock_quantity'])
        return 200, product
    except Product.DoesNotExist:
        return 400, ErrorSchema(message='المنتج غير موجود')


@router.get('/my-stores/{store_id}/products/low-stock', response=List[ProductListSchema])
def list_low_stock_products(request, store_id: UUID):
    """
    المنتجات منخفضة المخزون
    """
    from django.db.models import F
    return Product.objects.filter(
        store_id=store_id,
        store__owner=request.user,
        track_inventory=True,
        stock_quantity__lte=F('low_stock_threshold')
    )
