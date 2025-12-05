from src.models.user import db
from datetime import datetime

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(500))
    city = db.Column(db.String(100), nullable=False)
    logo_url = db.Column(db.String(500))
    rating = db.Column(db.Float, default=0.0)
    reviews_count = db.Column(db.Integer, default=0)
    verified = db.Column(db.Boolean, default=False)
    specialties = db.Column(db.Text)  # JSON string of specialties
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='supplier', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='supplier', lazy=True)

    def __repr__(self):
        return f'<Supplier {self.name}>'

    def to_dict(self):
        import json
        specialties_list = []
        if self.specialties:
            try:
                specialties_list = json.loads(self.specialties)
            except:
                specialties_list = []
                
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'logo_url': self.logo_url,
            'rating': self.rating,
            'reviews_count': self.reviews_count,
            'verified': self.verified,
            'specialties': specialties_list,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

