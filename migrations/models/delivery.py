from extensions import db
from datetime import datetime


class Delivery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order_tbl.id'), nullable=False)
    delivery_staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=True)
    status = db.Column(db.String(50), default='pending')
    assigned_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'delivery_staff_id': self.delivery_staff_id,
            'status': self.status,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None
        }
