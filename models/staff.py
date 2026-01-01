from extensions import db


class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    phone = db.Column(db.String(30), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_available = db.Column(db.Boolean, default=True)

    user = db.relationship('Users', backref=db.backref('staff_profile', uselist=False))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'phone': self.phone,
            'is_active': self.is_active,
            'is_available': self.is_available
        }
