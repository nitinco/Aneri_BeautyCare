from extensions import db
from datetime import datetime


class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Numeric(10, 2), default=0.00)
    tax_amount = db.Column(db.Numeric(10, 2), default=0.00)
    discount_amount = db.Column(db.Numeric(10, 2), default=0.00)
    status = db.Column(db.String(50), default='unpaid')

    details = db.relationship('BillDetail', backref='bill', lazy=True)
    payments = db.relationship('Payment', backref='bill', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'created_at': self.created_at.isoformat(),
            'total_amount': float(self.total_amount),
            'tax_amount': float(self.tax_amount),
            'discount_amount': float(self.discount_amount),
            'status': self.status,
            'details': [d.to_dict() for d in self.details]
        }


class BillDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bill.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)
    description = db.Column(db.String(255))
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Numeric(10, 2), default=0.00)
    amount = db.Column(db.Numeric(10, 2), default=0.00)

    def to_dict(self):
        return {
            'id': self.id,
            'bill_id': self.bill_id,
            'service_id': self.service_id,
            'product_id': self.product_id,
            'description': self.description,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'amount': float(self.amount)
        }


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bill.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), default=0.00)
    method = db.Column(db.String(50))
    provider = db.Column(db.String(50))
    provider_payment_id = db.Column(db.String(255))
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    charges = db.relationship('Charge', backref='payment', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'bill_id': self.bill_id,
            'amount': float(self.amount),
            'method': self.method,
            'provider': self.provider,
            'provider_payment_id': self.provider_payment_id,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'charges': [c.to_dict() for c in self.charges]
        }


class Charge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payment.id'), nullable=False)
    type = db.Column(db.String(50))
    amount = db.Column(db.Numeric(10, 2), default=0.00)
    description = db.Column(db.String(255))

    details = db.relationship('ChargeDetail', backref='charge', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'payment_id': self.payment_id,
            'type': self.type,
            'amount': float(self.amount),
            'description': self.description,
            'details': [d.to_dict() for d in self.details]
        }


class ChargeDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    charge_id = db.Column(db.Integer, db.ForeignKey('charge.id'), nullable=False)
    key_name = db.Column(db.String(100))
    key_value = db.Column(db.String(255))

    def to_dict(self):
        return {'id': self.id, 'charge_id': self.charge_id, 'key_name': self.key_name, 'key_value': self.key_value}
