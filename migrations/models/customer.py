from extensions import db


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    phone = db.Column(db.String(30), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    area_id = db.Column(db.Integer, db.ForeignKey('area.id'), nullable=True)

    user = db.relationship('Users', backref=db.backref('customer_profile', uselist=False))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'phone': self.phone,
            'address': self.address,
            'area_id': self.area_id
        }
