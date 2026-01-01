from extensions import db
from datetime import datetime


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('CartItem', backref='cart', lazy=True)

    def to_dict(self):
        return {'id': self.id, 'customer_id': self.customer_id, 'created_at': self.created_at.isoformat(), 'items': [i.to_dict() for i in self.items]}


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)

    def to_dict(self):
        return {'id': self.id, 'cart_id': self.cart_id, 'product_id': self.product_id, 'quantity': self.quantity}


class Order(db.Model):
    __tablename__ = 'order_tbl'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'), nullable=True)
    total_amount = db.Column(db.Numeric(10, 2), default=0.00)
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('OrderItem', backref='order', lazy=True)

    def to_dict(self):
        return {'id': self.id, 'customer_id': self.customer_id, 'cart_id': self.cart_id, 'total_amount': float(self.total_amount), 'status': self.status, 'items': [i.to_dict() for i in self.items]}


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order_tbl.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Numeric(10, 2), default=0.00)

    def to_dict(self):
        return {'id': self.id, 'order_id': self.order_id, 'product_id': self.product_id, 'quantity': self.quantity, 'unit_price': float(self.unit_price)}
