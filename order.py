from src.models.user import db
from datetime import datetime

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(200), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_address = db.Column(db.String(500), nullable=False)
    customer_city = db.Column(db.String(100), nullable=False)
    customer_type = db.Column(db.String(50), nullable=False)  # individual, company
    company_name = db.Column(db.String(200))  # if customer_type is company
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, shipped, delivered, cancelled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Order {self.order_number}>'

    def to_dict(self, include_items=False, include_supplier=False):
        result = {
            'id': self.id,
            'order_number': self.order_number,
            'customer_name': self.customer_name,
            'customer_email': self.customer_email,
            'customer_phone': self.customer_phone,
            'customer_address': self.customer_address,
            'customer_city': self.customer_city,
            'customer_type': self.customer_type,
            'company_name': self.company_name,
            'total_amount': self.total_amount,
            'status': self.status,
            'notes': self.notes,
            'supplier_id': self.supplier_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_items:
            result['items'] = [item.to_dict(include_product=True) for item in self.order_items]
            
        if include_supplier and self.supplier:
            result['supplier'] = self.supplier.to_dict()
            
        return result


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    
    # Foreign Keys
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

    def __repr__(self):
        return f'<OrderItem {self.id}>'

    def to_dict(self, include_product=False):
        result = {
            'id': self.id,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total_price': self.total_price,
            'notes': self.notes,
            'order_id': self.order_id,
            'product_id': self.product_id
        }
        
        if include_product and self.product:
            result['product'] = self.product.to_dict()
            
        return result

