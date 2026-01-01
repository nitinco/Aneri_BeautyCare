from extensions import db
from datetime import datetime


class Brand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255))

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'description': self.description}


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'), nullable=True)
    sku = db.Column(db.String(120))
    price = db.Column(db.Numeric(10, 2), default=0.00)
    is_active = db.Column(db.Boolean, default=True)

    brand = db.relationship('Brand', backref=db.backref('products', lazy=True))
    details = db.relationship('ProductDetail', backref='product', lazy=True)
    stocks = db.relationship('Stock', backref='product', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'brand_id': self.brand_id,
            'sku': self.sku,
            'price': float(self.price),
            'is_active': self.is_active
        }


class ProductDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    key_name = db.Column(db.String(100))
    key_value = db.Column(db.String(255))

    def to_dict(self):
        return {'id': self.id, 'product_id': self.product_id, 'key_name': self.key_name, 'key_value': self.key_value}


class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    contact = db.Column(db.String(120))
    address = db.Column(db.String(255))

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'contact': self.contact, 'address': self.address}


class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=True)
    quantity = db.Column(db.Integer, default=0)
    reorder_level = db.Column(db.Integer, default=5)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier = db.relationship('Supplier', backref=db.backref('stocks', lazy=True))

    def to_dict(self):
        return {'id': self.id, 'product_id': self.product_id, 'supplier_id': self.supplier_id, 'quantity': self.quantity, 'reorder_level': self.reorder_level}
