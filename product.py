from src.models.user import db
from datetime import datetime

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50), nullable=False)  # متر، كيلو، قطعة، etc.
    minimum_order = db.Column(db.Integer, default=1)
    stock_quantity = db.Column(db.Integer, default=0)
    sku = db.Column(db.String(100), unique=True)  # Stock Keeping Unit
    brand = db.Column(db.String(100))
    specifications = db.Column(db.Text)  # JSON string of specifications
    images = db.Column(db.Text)  # JSON string of image URLs
    featured = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='product', lazy=True)

    def __repr__(self):
        return f'<Product {self.name}>'

    def to_dict(self, include_supplier=False, include_category=False):
        import json
        
        specifications_dict = {}
        if self.specifications:
            try:
                specifications_dict = json.loads(self.specifications)
            except:
                specifications_dict = {}
                
        images_list = []
        if self.images:
            try:
                images_list = json.loads(self.images)
            except:
                images_list = []
        
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'unit': self.unit,
            'minimum_order': self.minimum_order,
            'stock_quantity': self.stock_quantity,
            'sku': self.sku,
            'brand': self.brand,
            'specifications': specifications_dict,
            'images': images_list,
            'featured': self.featured,
            'active': self.active,
            'supplier_id': self.supplier_id,
            'category_id': self.category_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_supplier and self.supplier:
            result['supplier'] = self.supplier.to_dict()
            
        if include_category and self.category:
            result['category'] = self.category.to_dict()
            
        return result

