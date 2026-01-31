from extensions import db


class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    duration_mins = db.Column(db.Integer, nullable=False, default=30)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('sub_category.id'), nullable=True)
    service_type = db.Column(db.String(50), nullable=False, default='in-center')  # 'in-center' or 'home'
    image = db.Column(db.String(255), nullable=True)  # Path to service image

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': float(self.price),
            'duration_mins': self.duration_mins,
            'category_id': self.subcategory.category_id if self.subcategory else None,
            'subcategory_id': self.subcategory_id,
            'service_type': self.service_type,
            'image': self.image
        }
