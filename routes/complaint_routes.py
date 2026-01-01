from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from extensions import db
from models import Complaint, Feedback

cmp_bp = Blueprint('complaint', __name__)


def admin_required():
    claims = get_jwt()
    return claims.get('role') == 'admin'


@cmp_bp.route('/complaints', methods=['POST'])
@jwt_required()
def submit_complaint():
    data = request.get_json() or {}
    c = Complaint(customer_id=data.get('customer_id'), subject=data.get('subject'), message=data.get('message'))
    db.session.add(c)
    db.session.commit()
    return jsonify(c.to_dict()), 201


@cmp_bp.route('/complaints', methods=['GET'])
@jwt_required()
def list_complaints():
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    return jsonify([c.to_dict() for c in Complaint.query.all()])


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
