from extensions import db
from datetime import date


class Offer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(255))
    is_product_offer = db.Column(db.Boolean, default=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=True)
    discount_percent = db.Column(db.Integer, default=0)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)

    def is_valid(self):
        today = date.today()
        if not self.is_active:
            return False
        if self.start_date and today < self.start_date:
            return False
        if self.end_date and today > self.end_date:
            return False
        return True

    def to_dict(self):
        from models import Product, Service  # Import here to avoid circular imports
        product_name = None
        service_name = None
        
        if self.product_id:
            product = Product.query.get(self.product_id)
            product_name = product.name if product else None
            
        if self.service_id:
            service = Service.query.get(self.service_id)
            service_name = service.name if service else None
            
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'is_product_offer': self.is_product_offer,
            'product_id': self.product_id,
            'product_name': product_name,
            'service_id': self.service_id,
            'service_name': service_name,
            'discount_percent': self.discount_percent,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_active': self.is_active
        }
