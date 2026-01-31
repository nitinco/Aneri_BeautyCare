from extensions import db
import datetime


class Package(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    is_active = db.Column(db.Boolean, default=True)
    details = db.relationship('PackageDetail', backref='package', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': float(self.price),
            'is_active': self.is_active,
            'details': [d.to_dict() for d in self.details]
        }


class PackageDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(db.Integer, db.ForeignKey('package.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    no_of_sitting = db.Column(db.Integer, nullable=False, default=1)

    def to_dict(self):
        return {'id': self.id, 'package_id': self.package_id, 'service_id': self.service_id, 'no_of_sitting': self.no_of_sitting}


class PackageBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    package_id = db.Column(db.Integer, db.ForeignKey('package.id'), nullable=False)
    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime, nullable=False)
    address = db.Column(db.String(255), nullable=True)  # For home service packages
    pincode = db.Column(db.String(20), nullable=True)
    service_type = db.Column(db.String(10), nullable=False, default='salon')  # salon or home
    status = db.Column(db.String(30), nullable=False, default='pending')  # pending, confirmed, completed, cancelled
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    razorpay_order_id = db.Column(db.String(100), nullable=True)
    razorpay_payment_id = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)

    customer = db.relationship('Customer', backref=db.backref('package_bookings', lazy=True))
    package = db.relationship('Package', backref=db.backref('bookings', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'package_id': self.package_id,
            'package_name': self.package.name if self.package else None,
            'start_datetime': self.start_datetime.isoformat() if self.start_datetime else None,
            'end_datetime': self.end_datetime.isoformat() if self.end_datetime else None,
            'address': self.address,
            'pincode': self.pincode,
            'service_type': self.service_type,
            'status': self.status,
            'total_amount': float(self.total_amount),
            'razorpay_order_id': self.razorpay_order_id,
            'razorpay_payment_id': self.razorpay_payment_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'notes': self.notes
        }
