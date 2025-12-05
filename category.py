from src.models.user import db
from datetime import datetime

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100))  # English name for reference
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))  # Icon name for frontend
    color = db.Column(db.String(20))  # Color code for UI
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Self-referential relationship for subcategories
    subcategories = db.relationship('Category', backref=db.backref('parent', remote_side=[id]), lazy=True)
    
    # Relationship with products
    products = db.relationship('Product', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'

    def to_dict(self, include_subcategories=False):
        result = {
            'id': self.id,
            'name': self.name,
            'name_en': self.name_en,
            'description': self.description,
            'icon': self.icon,
            'color': self.color,
            'parent_id': self.parent_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'products_count': len(self.products)
        }
        
        if include_subcategories:
            result['subcategories'] = [sub.to_dict() for sub in self.subcategories]
            
        return result

