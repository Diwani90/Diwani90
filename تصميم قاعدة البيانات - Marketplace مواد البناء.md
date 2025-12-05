# تصميم قاعدة البيانات - Marketplace مواد البناء

## الجداول الأساسية

### 1. جدول المستخدمين (Users)
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    user_type ENUM('admin', 'supplier', 'customer') NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. جدول الموردين (Suppliers)
```sql
CREATE TABLE suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    commercial_register VARCHAR(50),
    tax_number VARCHAR(50),
    business_license VARCHAR(255),
    description TEXT,
    address TEXT,
    city VARCHAR(100),
    region VARCHAR(100),
    postal_code VARCHAR(10),
    website VARCHAR(255),
    logo_url VARCHAR(255),
    is_verified BOOLEAN DEFAULT FALSE,
    rating DECIMAL(3,2) DEFAULT 0.00,
    total_reviews INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 3. جدول العملاء (Customers)
```sql
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    company_name VARCHAR(255),
    customer_type ENUM('individual', 'company') NOT NULL,
    address TEXT,
    city VARCHAR(100),
    region VARCHAR(100),
    postal_code VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 4. جدول الفئات (Categories)
```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    name_ar VARCHAR(255) NOT NULL,
    description TEXT,
    parent_id INTEGER,
    icon_url VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES categories(id)
);
```

### 5. جدول المنتجات (Products)
```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    specifications TEXT,
    price DECIMAL(10,2) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    minimum_order INTEGER DEFAULT 1,
    stock_quantity INTEGER DEFAULT 0,
    sku VARCHAR(100),
    brand VARCHAR(100),
    origin_country VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    featured BOOLEAN DEFAULT FALSE,
    rating DECIMAL(3,2) DEFAULT 0.00,
    total_reviews INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (category_id) REFERENCES categories(id)
);
```

### 6. جدول صور المنتجات (Product Images)
```sql
CREATE TABLE product_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    image_url VARCHAR(255) NOT NULL,
    alt_text VARCHAR(255),
    is_primary BOOLEAN DEFAULT FALSE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

### 7. جدول الطلبات (Orders)
```sql
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    status ENUM('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled') DEFAULT 'pending',
    total_amount DECIMAL(10,2) NOT NULL,
    notes TEXT,
    delivery_address TEXT,
    delivery_city VARCHAR(100),
    delivery_region VARCHAR(100),
    delivery_postal_code VARCHAR(10),
    requested_delivery_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);
```

### 8. جدول عناصر الطلبات (Order Items)
```sql
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

### 9. جدول المراجعات (Reviews)
```sql
CREATE TABLE reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    supplier_id INTEGER,
    product_id INTEGER,
    order_id INTEGER,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(255),
    comment TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    is_approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (order_id) REFERENCES orders(id)
);
```

### 10. جدول السلة (Cart)
```sql
CREATE TABLE cart_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    UNIQUE(customer_id, product_id)
);
```

## العلاقات بين الجداول

### علاقات رئيسية:
1. **User → Supplier/Customer**: علاقة واحد لواحد
2. **Supplier → Products**: علاقة واحد لمتعدد
3. **Category → Products**: علاقة واحد لمتعدد
4. **Product → Product Images**: علاقة واحد لمتعدد
5. **Customer → Orders**: علاقة واحد لمتعدد
6. **Supplier → Orders**: علاقة واحد لمتعدد
7. **Order → Order Items**: علاقة واحد لمتعدد
8. **Product → Order Items**: علاقة واحد لمتعدد
9. **Customer → Reviews**: علاقة واحد لمتعدد
10. **Customer → Cart Items**: علاقة واحد لمتعدد

## الفهارس المطلوبة

```sql
-- فهارس للبحث السريع
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_supplier ON products(supplier_id);
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_price ON products(price);
CREATE INDEX idx_products_active ON products(is_active);

CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_supplier ON orders(supplier_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_date ON orders(created_at);

CREATE INDEX idx_reviews_product ON reviews(product_id);
CREATE INDEX idx_reviews_supplier ON reviews(supplier_id);
CREATE INDEX idx_reviews_customer ON reviews(customer_id);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_type ON users(user_type);
```

## البيانات الأولية

### الفئات الأساسية:
1. الخرسانة والأسمنت
2. الحديد والصلب
3. الطوب والبلوك
4. العزل
5. الأبواب والنوافذ
6. السيراميك والبلاط
7. الدهانات والطلاء
8. السباكة والكهرباء

### المناطق السعودية:
- الرياض
- مكة المكرمة
- المدينة المنورة
- المنطقة الشرقية
- عسير
- تبوك
- حائل
- الحدود الشمالية
- جازان
- نجران
- الباحة
- الجوف
- القصيم

