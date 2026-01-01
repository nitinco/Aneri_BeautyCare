from extensions import db
from datetime import datetime


class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    subject = db.Column(db.String(200))
    message = db.Column(db.Text)
    status = db.Column(db.String(50), default='open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def to_dict(self):
        return {'id': self.id, 'customer_id': self.customer_id, 'subject': self.subject, 'message': self.message, 'status': self.status, 'created_at': self.created_at.isoformat(), 'reviewed_by': self.reviewed_by}


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    rating = db.Column(db.Integer, default=5)
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {'id': self.id, 'customer_id': self.customer_id, 'rating': self.rating, 'message': self.message, 'created_at': self.created_at.isoformat()}
