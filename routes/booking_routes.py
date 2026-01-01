from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import db
from models import Service, Appointment, Booking, Customer, Staff
import datetime

booking_bp = Blueprint('booking', __name__)


def role_from_jwt():
    claims = get_jwt()
    return claims.get('role')


def parse_datetime(date_str, time_str):
    # date_str: YYYY-MM-DD, time_str: HH:MM
    return datetime.datetime.fromisoformat(f"{date_str}T{time_str}:00")


def overlaps(start1, end1, start2, end2):
    return start1 < end2 and start2 < end1


@booking_bp.route('/slots', methods=['GET'])
def available_slots():
    # params: service_id, date (YYYY-MM-DD)
    service_id = request.args.get('service_id')
    date = request.args.get('date')
    if not service_id or not date:
        return jsonify({'message': 'service_id and date required'}), 400

    svc = Service.query.get(service_id)
    if not svc:
        return jsonify({'message': 'service not found'}), 404

    # Basic working hours and slot interval
    WORK_START = 9
    WORK_END = 18
    INTERVAL = 30  # minutes

    slots = []
    dt = datetime.date.fromisoformat(date)
    start_dt = datetime.datetime(dt.year, dt.month, dt.day, WORK_START, 0)
    end_dt = datetime.datetime(dt.year, dt.month, dt.day, WORK_END, 0)
    cur = start_dt
    # collect staff list
    staffs = Staff.query.filter_by(is_available=True, is_active=True).all()

    while cur + datetime.timedelta(minutes=svc.duration_mins) <= end_dt:
        slot_end = cur + datetime.timedelta(minutes=svc.duration_mins)
        # check if any staff is free for this slot
        free_staff_ids = []
        for staff in staffs:
            # check appointments overlapping with this slot
            conflict = Appointment.query.filter(
                Appointment.staff_id == staff.id,
                Appointment.status.in_(['approved','pending']),
                db.or_(
                    db.and_(Appointment.start_datetime <= cur, Appointment.end_datetime > cur),
                    db.and_(Appointment.start_datetime < slot_end, Appointment.end_datetime >= slot_end),
                    db.and_(Appointment.start_datetime >= cur, Appointment.end_datetime <= slot_end),
                )
            ).first()
            if not conflict:
                free_staff_ids.append(staff.id)

        if free_staff_ids:
            slots.append({'start': cur.isoformat(), 'end': slot_end.isoformat(), 'available_staff': free_staff_ids})

        cur += datetime.timedelta(minutes=INTERVAL)

    return jsonify(slots)


@booking_bp.route('/appointments', methods=['POST'])
@jwt_required()
def create_appointment():
    uid = get_jwt_identity()
    try:
        user_id = int(uid)
    except Exception:
        return jsonify({'message': 'invalid token identity'}), 400
    # find customer by user_id
    customer = Customer.query.filter_by(user_id=user_id).first()
    if not customer:
        return jsonify({'message': 'Customer profile required'}), 400

    data = request.get_json() or {}
    service_id = data.get('service_id')
    date = data.get('date')
    time = data.get('time')
    staff_id = data.get('staff_id')

    if not service_id or not date or not time:
        return jsonify({'message': 'service_id, date and time required'}), 400

    svc = Service.query.get(service_id)
    if not svc:
        return jsonify({'message': 'service not found'}), 404

    start_dt = parse_datetime(date, time)
    end_dt = start_dt + datetime.timedelta(minutes=svc.duration_mins)

    # if staff provided, check availability
    assigned_staff = None
    if staff_id:
        st = Staff.query.get(staff_id)
        if not st or not st.is_active or not st.is_available:
            return jsonify({'message': 'staff not available'}), 400
        conflict = Appointment.query.filter(
            Appointment.staff_id == st.id,
            Appointment.status.in_(['approved','pending']),
            db.or_(
                db.and_(Appointment.start_datetime <= start_dt, Appointment.end_datetime > start_dt),
                db.and_(Appointment.start_datetime < end_dt, Appointment.end_datetime >= end_dt),
                db.and_(Appointment.start_datetime >= start_dt, Appointment.end_datetime <= end_dt),
            )
        ).first()
        if conflict:
            return jsonify({'message': 'staff has conflicting appointment'}), 400
        assigned_staff = st
    else:
        # auto-assign first free staff
        st = Staff.query.filter_by(is_active=True, is_available=True).all()
        for candidate in st:
            conflict = Appointment.query.filter(
                Appointment.staff_id == candidate.id,
                Appointment.status.in_(['approved','pending']),
                db.or_(
                    db.and_(Appointment.start_datetime <= start_dt, Appointment.end_datetime > start_dt),
                    db.and_(Appointment.start_datetime < end_dt, Appointment.end_datetime >= end_dt),
                    db.and_(Appointment.start_datetime >= start_dt, Appointment.end_datetime <= end_dt),
                )
            ).first()
            if not conflict:
                assigned_staff = candidate
                break

    appt = Appointment(customer_id=customer.id, staff_id=assigned_staff.id if assigned_staff else None,
                       service_id=svc.id, start_datetime=start_dt, end_datetime=end_dt, status='pending')
    db.session.add(appt)
    db.session.commit()
    return jsonify({'appointment': appt.to_dict()}), 201


@booking_bp.route('/bookings', methods=['POST'])
@jwt_required()
def create_booking():
    uid = get_jwt_identity()
    try:
        user_id = int(uid)
    except Exception:
        return jsonify({'message': 'invalid token identity'}), 400
    customer = Customer.query.filter_by(user_id=user_id).first()
    if not customer:
        return jsonify({'message': 'Customer profile required'}), 400

    data = request.get_json() or {}
    service_id = data.get('service_id')
    date = data.get('date')
    time = data.get('time')
    address = data.get('address')
    pincode = data.get('pincode')

    if not service_id or not date or not time or not address:
        return jsonify({'message': 'service_id, date, time, address required'}), 400

    svc = Service.query.get(service_id)
    if not svc:
        return jsonify({'message': 'service not found'}), 404

    start_dt = parse_datetime(date, time)
    end_dt = start_dt + datetime.timedelta(minutes=svc.duration_mins)

    # Compute home charge: simple rule — if pincode matches an Area in DB, zero charge else fixed 200
    from models import Area
    area = Area.query.filter_by(pincode=pincode).first() if pincode else None
    home_charge = 0.0 if area else 200.0

    # assign staff same as appointment auto-assign logic
    assigned_staff = None
    for candidate in Staff.query.filter_by(is_active=True, is_available=True).all():
        conflict = Appointment.query.filter(
            Appointment.staff_id == candidate.id,
            Appointment.status.in_(['approved','pending']),
            db.or_(
                db.and_(Appointment.start_datetime <= start_dt, Appointment.end_datetime > start_dt),
                db.and_(Appointment.start_datetime < end_dt, Appointment.end_datetime >= end_dt),
                db.and_(Appointment.start_datetime >= start_dt, Appointment.end_datetime <= end_dt),
            )
        ).first()
        if not conflict:
            assigned_staff = candidate
            break

    booking = Booking(customer_id=customer.id, service_id=svc.id, start_datetime=start_dt,
                      end_datetime=end_dt, address=address, pincode=pincode, home_charge=home_charge,
                      staff_id=assigned_staff.id if assigned_staff else None, status='pending')

    db.session.add(booking)
    db.session.commit()
    return jsonify({'booking': booking.to_dict()}), 201


@booking_bp.route('/appointments/<int:appt_id>/approve', methods=['POST'])
@jwt_required()
def approve_appointment(appt_id):
    if role_from_jwt() != 'admin':
        return jsonify({'message': 'admin required'}), 403
    appt = Appointment.query.get(appt_id)
    if not appt:
        return jsonify({'message': 'appointment not found'}), 404
    appt.status = 'approved'
    db.session.commit()
    return jsonify({'appointment': appt.to_dict()}), 200


@booking_bp.route('/appointments/<int:appt_id>/reject', methods=['POST'])
@jwt_required()
def reject_appointment(appt_id):
    if role_from_jwt() != 'admin':
        return jsonify({'message': 'admin required'}), 403
    appt = Appointment.query.get(appt_id)
    if not appt:
        return jsonify({'message': 'appointment not found'}), 404
    appt.status = 'rejected'
    db.session.commit()
    return jsonify({'appointment': appt.to_dict()}), 200


@booking_bp.route('/staff/jobs', methods=['GET'])
@jwt_required()
def staff_jobs():
    if role_from_jwt() != 'staff':
        return jsonify({'message': 'staff role required'}), 403
    uid = get_jwt_identity()
    try:
        user_id = int(uid)
    except Exception:
        return jsonify({'message': 'invalid token identity'}), 400
    # find staff by user_id
    st = Staff.query.filter_by(user_id=user_id).first()
    if not st:
        return jsonify({'message': 'staff profile not found'}), 404
    jobs = Appointment.query.filter_by(staff_id=st.id, status='approved').all()
    return jsonify([j.to_dict() for j in jobs])


@booking_bp.route('/staff/me/assignments', methods=['GET'])
@jwt_required()
def staff_assignments():
    # returns combined appointments and bookings assigned to the logged-in staff
    if role_from_jwt() != 'staff':
        return jsonify({'message': 'staff role required'}), 403
    uid = get_jwt_identity()
    try:
        user_id = int(uid)
    except Exception:
        return jsonify({'message': 'invalid token identity'}), 400
    st = Staff.query.filter_by(user_id=user_id).first()
    if not st:
        return jsonify({'message': 'staff profile not found'}), 404

    # get appointments and bookings assigned to this staff (pending or approved or in-progress)
    appts = Appointment.query.filter(Appointment.staff_id == st.id).all()
    bookings = Booking.query.filter(Booking.staff_id == st.id).all()

    out = []
    for a in appts:
        try:
            customer_name = a.customer.user.name if a.customer and a.customer.user else None
        except Exception:
            customer_name = None
        out.append({
            'type': 'appointment',
            'id': a.id,
            'customer_name': customer_name,
            'service_id': a.service_id,
            'service_name': a.service.name if a.service else None,
            'start_datetime': a.start_datetime.isoformat() if a.start_datetime else None,
            'end_datetime': a.end_datetime.isoformat() if a.end_datetime else None,
            'location': 'salon',
            'status': a.status
        })

    for b in bookings:
        try:
            customer_name = b.customer.user.name if b.customer and b.customer.user else None
        except Exception:
            customer_name = None
        out.append({
            'type': 'booking',
            'id': b.id,
            'customer_name': customer_name,
            'service_id': b.service_id,
            'service_name': b.service.name if b.service else None,
            'start_datetime': b.start_datetime.isoformat() if b.start_datetime else None,
            'end_datetime': b.end_datetime.isoformat() if b.end_datetime else None,
            'location': 'home',
            'status': b.status
        })

    # sort by start_datetime
    def _key(x):
        try:
            return x.get('start_datetime') or ''
        except Exception:
            return ''

    out_sorted = sorted(out, key=_key)
    return jsonify(out_sorted)


@booking_bp.route('/my/appointments', methods=['GET'])
@jwt_required()
def my_appointments():
    uid = get_jwt_identity()
    try:
        user_id = int(uid)
    except Exception:
        return jsonify({'message': 'invalid token identity'}), 400
    customer = Customer.query.filter_by(user_id=user_id).first()
    if not customer:
        return jsonify({'message': 'customer profile not found'}), 404
    appts = Appointment.query.filter_by(customer_id=customer.id).order_by(Appointment.start_datetime.desc()).all()
    return jsonify([a.to_dict() for a in appts])


@booking_bp.route('/appointments/pending', methods=['GET'])
@jwt_required()
def pending_appointments():
    # admin only
    if role_from_jwt() != 'admin':
        return jsonify({'message': 'admin required'}), 403
    appts = Appointment.query.filter_by(status='pending').order_by(Appointment.start_datetime.asc()).all()
    return jsonify([a.to_dict() for a in appts])


@booking_bp.route('/appointments', methods=['GET'])
@jwt_required()
def list_appointments_all():
    # allow admin and staff to view appointments; support optional date filter (YYYY-MM-DD)
    if role_from_jwt() not in ('admin', 'staff'):
        return jsonify({'message': 'forbidden'}), 403
    date_str = request.args.get('date')
    q = Appointment.query
    if date_str:
        try:
            dt = datetime.date.fromisoformat(date_str)
            start = datetime.datetime(dt.year, dt.month, dt.day, 0, 0)
            end = start + datetime.timedelta(days=1)
            q = q.filter(Appointment.start_datetime >= start, Appointment.start_datetime < end)
        except Exception:
            return jsonify({'message': 'invalid date format'}), 400
    appts = q.order_by(Appointment.start_datetime.asc()).all()
    out = []
    for a in appts:
        d = a.to_dict()
        # enrich with related names when available
        try:
            d['customer_name'] = a.customer.user.name if a.customer and a.customer.user else None
        except Exception:
            d['customer_name'] = None
        try:
            d['service_name'] = a.service.name if a.service else None
        except Exception:
            d['service_name'] = None
        try:
            # prefer staff user name when available
            d['staff_name'] = a.staff.user.name if a.staff and getattr(a.staff, 'user', None) else None
        except Exception:
            # fallback to staff id
            d['staff_name'] = None
        try:
            # human-friendly created timestamp for admin view
            d['created_display'] = a.created_at.strftime('%Y-%m-%d %H:%M') if a.created_at else None
        except Exception:
            d['created_display'] = None
        out.append(d)
    return jsonify(out)
