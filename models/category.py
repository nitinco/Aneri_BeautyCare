from extensions import db


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    subcategories = db.relationship('SubCategory', backref='category', lazy=True)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "description": self.description}


class SubCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    description = db.Column(db.Text, nullable=True)
    services = db.relationship('Service', backref='subcategory', lazy=True)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "category_id": self.category_id, "description": self.description}
