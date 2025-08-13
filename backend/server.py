from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, File, UploadFile, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from bson import ObjectId
import json
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Create the main app
app = FastAPI(title="منصة مواد البناء", description="منصة رقمية شاملة لمواد البناء في السعودية")
api_router = APIRouter(prefix="/api")

# Enums
class UserRole(str, Enum):
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    ADMIN = "admin"

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class ChatMessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"

# Categories for construction materials
CATEGORIES = [
    {"id": "concrete", "name": "خرسانة جاهزة", "name_en": "Ready Mix Concrete"},
    {"id": "rebar", "name": "حديد مسلح", "name_en": "Reinforced Steel"},
    {"id": "steel", "name": "حديد تصنيع", "name_en": "Manufacturing Steel"},
    {"id": "blocks", "name": "بلوك وطوب", "name_en": "Blocks and Bricks"},
    {"id": "wood", "name": "خشب ومواد النجارة", "name_en": "Wood and Carpentry"},
    {"id": "sand", "name": "رمل وحصى", "name_en": "Sand and Gravel"},
    {"id": "plumbing", "name": "مواد سباكة ولوازمها", "name_en": "Plumbing Materials"},
    {"id": "electrical", "name": "مواد كهرباء ولوازمها", "name_en": "Electrical Materials"},
    {"id": "paints", "name": "دهانات ومواد التشطيب", "name_en": "Paints and Finishing"},
    {"id": "ceramics", "name": "سيراميك وبورسلين وأنواعه", "name_en": "Ceramics and Porcelain"},
    {"id": "kitchens", "name": "مطابخ ولوازمها", "name_en": "Kitchens and Accessories"},
    {"id": "insulation", "name": "مواد عزل (حراري ومائي)", "name_en": "Insulation Materials"},
    {"id": "tools", "name": "أدوات وعدد كهربائية", "name_en": "Electric Tools"},
    {"id": "general", "name": "مواد بناء عامة", "name_en": "General Construction Materials"}
]

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    phone: str
    role: UserRole
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Customer specific fields
    delivery_address: Optional[str] = None
    city: Optional[str] = None
    
    # Supplier specific fields
    company_name: Optional[str] = None
    commercial_registration: Optional[str] = None
    tax_number: Optional[str] = None
    business_description: Optional[str] = None
    categories: List[str] = []
    location: Optional[Dict[str, float]] = None  # {"lat": 24.7136, "lng": 46.6753}
    rating: float = 0.0
    total_reviews: int = 0

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: str
    role: UserRole
    delivery_address: Optional[str] = None
    city: Optional[str] = None
    company_name: Optional[str] = None
    commercial_registration: Optional[str] = None
    tax_number: Optional[str] = None
    business_description: Optional[str] = None
    categories: List[str] = []
    location: Optional[Dict[str, float]] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    supplier_id: str
    name: str
    description: str
    category: str
    price: float
    unit: str  # meter, kg, piece, etc.
    minimum_order: int = 1
    available_quantity: int
    images: List[str] = []
    specifications: Dict[str, Any] = {}
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # SEO and search
    keywords: List[str] = []
    rating: float = 0.0
    total_reviews: int = 0
    total_sold: int = 0

class ProductCreate(BaseModel):
    name: str
    description: str
    category: str
    price: float
    unit: str
    minimum_order: int = 1
    available_quantity: int
    images: List[str] = []
    specifications: Dict[str, Any] = {}
    keywords: List[str] = []

class CartItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    product_id: str
    quantity: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    supplier_id: str
    items: List[Dict[str, Any]]  # product_id, quantity, price, name
    total_amount: float
    status: OrderStatus = OrderStatus.PENDING
    delivery_address: str
    delivery_notes: Optional[str] = None
    estimated_delivery: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class OrderCreate(BaseModel):
    supplier_id: str
    items: List[Dict[str, Any]]
    delivery_address: str
    delivery_notes: Optional[str] = None

class Review(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    product_id: Optional[str] = None
    supplier_id: Optional[str] = None
    order_id: str
    rating: int  # 1-5
    comment: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ReviewCreate(BaseModel):
    product_id: Optional[str] = None
    supplier_id: Optional[str] = None
    order_id: str
    rating: int
    comment: str

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    sender_id: str
    receiver_id: str
    message_type: ChatMessageType = ChatMessageType.TEXT
    content: str
    file_url: Optional[str] = None
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChatMessageCreate(BaseModel):
    receiver_id: str
    message_type: ChatMessageType = ChatMessageType.TEXT
    content: str
    file_url: Optional[str] = None

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"id": user_id})
    if user is None:
        raise credentials_exception
    return User(**user)

# API Routes

# Authentication
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user
    user_dict = user_data.dict()
    del user_dict["password"]
    user = User(**user_dict)
    
    # Save to database
    await db.users.insert_one(user.dict())
    await db.user_passwords.insert_one({"user_id": user.id, "password": hashed_password})
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@api_router.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    user = await db.users.find_one({"email": user_credentials.email})
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    user_password = await db.user_passwords.find_one({"user_id": user["id"]})
    if not verify_password(user_credentials.password, user_password["password"]):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["id"]}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer", "user": User(**user)}

@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

# Categories
@api_router.get("/categories")
async def get_categories():
    return {"categories": CATEGORIES}

# Products
@api_router.post("/products", response_model=Product)
async def create_product(product_data: ProductCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.SUPPLIER:
        raise HTTPException(status_code=403, detail="Only suppliers can create products")
    
    product = Product(**product_data.dict(), supplier_id=current_user.id)
    await db.products.insert_one(product.dict())
    return product

@api_router.get("/products", response_model=List[Product])
async def get_products(
    category: Optional[str] = None,
    supplier_id: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    city: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    query = {"is_active": True}
    
    if category:
        query["category"] = category
    if supplier_id:
        query["supplier_id"] = supplier_id
    if min_price is not None:
        query["price"] = {"$gte": min_price}
    if max_price is not None:
        if "price" in query:
            query["price"]["$lte"] = max_price
        else:
            query["price"] = {"$lte": max_price}
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"keywords": {"$in": [search]}}
        ]
    
    products = await db.products.find(query).skip(skip).limit(limit).to_list(limit)
    return [Product(**product) for product in products]

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    product = await db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**product)

@api_router.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: str, product_data: ProductCreate, current_user: User = Depends(get_current_user)):
    product = await db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product["supplier_id"] != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to update this product")
    
    update_data = product_data.dict()
    update_data["updated_at"] = datetime.utcnow()
    
    await db.products.update_one({"id": product_id}, {"$set": update_data})
    updated_product = await db.products.find_one({"id": product_id})
    return Product(**updated_product)

# Cart
@api_router.post("/cart/add")
async def add_to_cart(product_id: str, quantity: int, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="Only customers can add to cart")
    
    # Check if product exists
    product = await db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if item already in cart
    existing_item = await db.cart_items.find_one({"customer_id": current_user.id, "product_id": product_id})
    if existing_item:
        await db.cart_items.update_one(
            {"id": existing_item["id"]}, 
            {"$set": {"quantity": existing_item["quantity"] + quantity}}
        )
    else:
        cart_item = CartItem(customer_id=current_user.id, product_id=product_id, quantity=quantity)
        await db.cart_items.insert_one(cart_item.dict())
    
    return {"message": "Item added to cart"}

@api_router.get("/cart")
async def get_cart(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="Only customers can view cart")
    
    cart_items = await db.cart_items.find({"customer_id": current_user.id}).to_list(100)
    
    # Get product details for each item
    enriched_items = []
    for item in cart_items:
        product = await db.products.find_one({"id": item["product_id"]})
        if product:
            enriched_items.append({
                "cart_item": CartItem(**item),
                "product": Product(**product),
                "total_price": product["price"] * item["quantity"]
            })
    
    return {"items": enriched_items}

@api_router.delete("/cart/{item_id}")
async def remove_from_cart(item_id: str, current_user: User = Depends(get_current_user)):
    result = await db.cart_items.delete_one({"id": item_id, "customer_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return {"message": "Item removed from cart"}

# Orders
@api_router.post("/orders", response_model=Order)
async def create_order(order_data: OrderCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="Only customers can create orders")
    
    # Calculate total amount
    total_amount = sum(item["price"] * item["quantity"] for item in order_data.items)
    
    order = Order(
        customer_id=current_user.id,
        supplier_id=order_data.supplier_id,
        items=order_data.items,
        total_amount=total_amount,
        delivery_address=order_data.delivery_address,
        delivery_notes=order_data.delivery_notes
    )
    
    await db.orders.insert_one(order.dict())
    
    # Remove items from cart if they exist
    for item in order_data.items:
        await db.cart_items.delete_many({"customer_id": current_user.id, "product_id": item["product_id"]})
    
    return order

@api_router.get("/orders", response_model=List[Order])
async def get_orders(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.CUSTOMER:
        query = {"customer_id": current_user.id}
    elif current_user.role == UserRole.SUPPLIER:
        query = {"supplier_id": current_user.id}
    else:  # Admin
        query = {}
    
    orders = await db.orders.find(query).sort("created_at", -1).to_list(100)
    return [Order(**order) for order in orders]

@api_router.put("/orders/{order_id}/status")
async def update_order_status(order_id: str, status: OrderStatus, current_user: User = Depends(get_current_user)):
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if current_user.role == UserRole.SUPPLIER and order["supplier_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this order")
    
    await db.orders.update_one(
        {"id": order_id}, 
        {"$set": {"status": status, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Order status updated"}

# Reviews
@api_router.post("/reviews", response_model=Review)
async def create_review(review_data: ReviewCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="Only customers can create reviews")
    
    # Check if order exists and belongs to customer
    order = await db.orders.find_one({"id": review_data.order_id, "customer_id": current_user.id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    review = Review(**review_data.dict(), customer_id=current_user.id)
    await db.reviews.insert_one(review.dict())
    
    # Update product/supplier rating
    if review_data.product_id:
        await update_product_rating(review_data.product_id)
    if review_data.supplier_id:
        await update_supplier_rating(review_data.supplier_id)
    
    return review

async def update_product_rating(product_id: str):
    reviews = await db.reviews.find({"product_id": product_id}).to_list(1000)
    if reviews:
        avg_rating = sum(r["rating"] for r in reviews) / len(reviews)
        await db.products.update_one(
            {"id": product_id}, 
            {"$set": {"rating": avg_rating, "total_reviews": len(reviews)}}
        )

async def update_supplier_rating(supplier_id: str):
    reviews = await db.reviews.find({"supplier_id": supplier_id}).to_list(1000)
    if reviews:
        avg_rating = sum(r["rating"] for r in reviews) / len(reviews)
        await db.users.update_one(
            {"id": supplier_id}, 
            {"$set": {"rating": avg_rating, "total_reviews": len(reviews)}}
        )

# Chat
@api_router.post("/chat/send", response_model=ChatMessage)
async def send_message(message_data: ChatMessageCreate, current_user: User = Depends(get_current_user)):
    conversation_id = f"{min(current_user.id, message_data.receiver_id)}_{max(current_user.id, message_data.receiver_id)}"
    
    message = ChatMessage(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        receiver_id=message_data.receiver_id,
        message_type=message_data.message_type,
        content=message_data.content,
        file_url=message_data.file_url
    )
    
    await db.chat_messages.insert_one(message.dict())
    return message

@api_router.get("/chat/conversations")
async def get_conversations(current_user: User = Depends(get_current_user)):
    # Get all conversations for current user
    messages = await db.chat_messages.find({
        "$or": [{"sender_id": current_user.id}, {"receiver_id": current_user.id}]
    }).sort("created_at", -1).to_list(1000)
    
    # Group by conversation
    conversations = {}
    for message in messages:
        conv_id = message["conversation_id"]
        if conv_id not in conversations:
            other_user_id = message["sender_id"] if message["receiver_id"] == current_user.id else message["receiver_id"]
            other_user = await db.users.find_one({"id": other_user_id})
            conversations[conv_id] = {
                "conversation_id": conv_id,
                "other_user": User(**other_user) if other_user else None,
                "last_message": ChatMessage(**message),
                "unread_count": 0
            }
        
        # Count unread messages
        if message["receiver_id"] == current_user.id and not message["is_read"]:
            conversations[conv_id]["unread_count"] += 1
    
    return {"conversations": list(conversations.values())}

@api_router.get("/chat/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str, current_user: User = Depends(get_current_user)):
    messages = await db.chat_messages.find({"conversation_id": conversation_id}).sort("created_at", 1).to_list(1000)
    
    # Mark messages as read
    await db.chat_messages.update_many(
        {"conversation_id": conversation_id, "receiver_id": current_user.id},
        {"$set": {"is_read": True}}
    )
    
    return {"messages": [ChatMessage(**msg) for msg in messages]}

# Suppliers
@api_router.get("/suppliers", response_model=List[User])
async def get_suppliers(
    category: Optional[str] = None,
    city: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    query = {"role": UserRole.SUPPLIER, "is_active": True}
    
    if category:
        query["categories"] = {"$in": [category]}
    if city:
        query["city"] = city
    if search:
        query["$or"] = [
            {"company_name": {"$regex": search, "$options": "i"}},
            {"business_description": {"$regex": search, "$options": "i"}}
        ]
    
    suppliers = await db.users.find(query).skip(skip).limit(limit).to_list(limit)
    return [User(**supplier) for supplier in suppliers]

@api_router.get("/suppliers/{supplier_id}", response_model=User)
async def get_supplier(supplier_id: str):
    supplier = await db.users.find_one({"id": supplier_id, "role": UserRole.SUPPLIER})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return User(**supplier)

# Statistics and Dashboard
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.CUSTOMER:
        total_orders = await db.orders.count_documents({"customer_id": current_user.id})
        pending_orders = await db.orders.count_documents({"customer_id": current_user.id, "status": OrderStatus.PENDING})
        cart_items = await db.cart_items.count_documents({"customer_id": current_user.id})
        
        return {
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "cart_items": cart_items
        }
    
    elif current_user.role == UserRole.SUPPLIER:
        total_products = await db.products.count_documents({"supplier_id": current_user.id})
        total_orders = await db.orders.count_documents({"supplier_id": current_user.id})
        pending_orders = await db.orders.count_documents({"supplier_id": current_user.id, "status": OrderStatus.PENDING})
        total_revenue = await db.orders.aggregate([
            {"$match": {"supplier_id": current_user.id, "status": {"$in": [OrderStatus.DELIVERED, OrderStatus.CONFIRMED]}}},
            {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}
        ]).to_list(1)
        
        return {
            "total_products": total_products,
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "total_revenue": total_revenue[0]["total"] if total_revenue else 0
        }
    
    else:  # Admin
        total_users = await db.users.count_documents({})
        total_suppliers = await db.users.count_documents({"role": UserRole.SUPPLIER})
        total_customers = await db.users.count_documents({"role": UserRole.CUSTOMER})
        total_products = await db.products.count_documents({})
        total_orders = await db.orders.count_documents({})
        
        return {
            "total_users": total_users,
            "total_suppliers": total_suppliers,
            "total_customers": total_customers,
            "total_products": total_products,
            "total_orders": total_orders
        }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()