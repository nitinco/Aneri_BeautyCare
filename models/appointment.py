from extensions import db
import datetime


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(30), nullable=False, default='pending')  # pending, approved, rejected, cancelled, completed
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    service_type = db.Column(db.String(10), nullable=False, default='salon')  # salon or home

    customer = db.relationship('Customer', backref=db.backref('appointments', lazy=True))
    staff = db.relationship('Staff', backref=db.backref('appointments', lazy=True))
    service = db.relationship('Service')

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'staff_id': self.staff_id,
            'service_id': self.service_id,
            'start_datetime': self.start_datetime.isoformat() if self.start_datetime else None,
            'end_datetime': self.end_datetime.isoformat() if self.end_datetime else None,
            'status': self.status,
            'service_type': self.service_type,  # Include service_type in the dictionary
        }


class AppointmentDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)
    notes = db.Column(db.Text, nullable=True)

    appointment = db.relationship('Appointment', backref=db.backref('details', lazy=True))

    def to_dict(self):
        return {'id': self.id, 'appointment_id': self.appointment_id, 'notes': self.notes}


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    pincode = db.Column(db.String(20), nullable=True)
    home_charge = db.Column(db.Numeric(10,2), nullable=False, default=0.0)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=True)
    status = db.Column(db.String(30), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    customer = db.relationship('Customer', backref=db.backref('bookings', lazy=True))
    staff = db.relationship('Staff')
    service = db.relationship('Service')

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'service_id': self.service_id,
            'start_datetime': self.start_datetime.isoformat(),
            'end_datetime': self.end_datetime.isoformat(),
            'address': self.address,
            'pincode': self.pincode,
            'home_charge': float(self.home_charge),
            'staff_id': self.staff_id,
            'status': self.status
        }


class BookingDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    notes = db.Column(db.Text, nullable=True)

    booking = db.relationship('Booking', backref=db.backref('details', lazy=True))

    def to_dict(self):
        return {'id': self.id, 'booking_id': self.booking_id, 'notes': self.notes}
