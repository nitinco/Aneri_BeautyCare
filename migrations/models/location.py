from extensions import db


class State(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    cities = db.relationship('City', backref='state', lazy=True)


class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    state_id = db.Column(db.Integer, db.ForeignKey('state.id'), nullable=False)
    areas = db.relationship('Area', backref='city', lazy=True)


class Area(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pincode = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(150), nullable=True)
    city_id = db.Column(db.Integer, db.ForeignKey('city.id'), nullable=False)
