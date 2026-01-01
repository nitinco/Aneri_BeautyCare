from extensions import db


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
    quantity = db.Column(db.Integer, nullable=False, default=1)

    def to_dict(self):
        return {'id': self.id, 'package_id': self.package_id, 'service_id': self.service_id, 'quantity': self.quantity}
