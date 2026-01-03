from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from models import Complaint, Feedback, Customer
from extensions import db
from models import Complaint, Feedback

cmp_bp = Blueprint('complaint', __name__)


def admin_required():
    claims = get_jwt()
    return claims.get('role') == 'admin'


@cmp_bp.route('/complaints', methods=['POST'])
@jwt_required()
def submit_complaint():
    uid = get_jwt_identity()
    try:
        user_id = int(uid)
    except Exception:
        return jsonify({'message': 'invalid token identity'}), 400
    cust = Customer.query.filter_by(user_id=user_id).first()
    if not cust:
        return jsonify({'message': 'customer profile not found'}), 400
    data = request.get_json() or {}
    c = Complaint(customer_id=cust.id, subject=data.get('subject'), message=data.get('message'))
    db.session.add(c)
    db.session.commit()
    return jsonify(c.to_dict()), 201


@cmp_bp.route('/complaints/me', methods=['GET'])
@jwt_required()
def my_complaints():
    uid = get_jwt_identity()
    try:
        user_id = int(uid)
    except Exception:
        return jsonify({'message': 'invalid token identity'}), 400
    cust = Customer.query.filter_by(user_id=user_id).first()
    if not cust:
        return jsonify({'message': 'customer profile not found'}), 400
    comps = Complaint.query.filter_by(customer_id=cust.id).all()
    out = []
    for c in comps:
        d = c.to_dict()
        out.append(d)
    return jsonify(out)


@cmp_bp.route('/complaints', methods=['GET'])
@jwt_required()
def list_complaints():
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    out = []
    for c in Complaint.query.all():
        d = c.to_dict()
        # try to add customer name/email if available
        try:
            cust = Customer.query.get(c.customer_id)
            if cust and getattr(cust, 'user', None):
                d['customer_name'] = cust.user.name
                d['customer_email'] = cust.user.email
            elif cust:
                d['customer_name'] = None
                d['customer_email'] = None
        except Exception:
            d['customer_name'] = None
            d['customer_email'] = None
        out.append(d)
    return jsonify(out)


@cmp_bp.route('/complaints/<int:complaint_id>/review', methods=['PUT'])
@jwt_required()
def review_complaint(complaint_id):
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    data = request.get_json() or {}
    c = Complaint.query.get(complaint_id)
    if not c:
        return jsonify({'message': 'not found'}), 404
    c.status = data.get('status', c.status)
    c.reviewed_by = data.get('reviewed_by')
    db.session.commit()
    return jsonify(c.to_dict())


@cmp_bp.route('/feedback', methods=['POST'])
@jwt_required()
def submit_feedback():
    data = request.get_json() or {}
    f = Feedback(customer_id=data.get('customer_id'), rating=data.get('rating',5), message=data.get('message'))
    db.session.add(f)
    db.session.commit()
    return jsonify(f.to_dict()), 201
