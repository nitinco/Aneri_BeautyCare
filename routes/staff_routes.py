from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from extensions import db
from models.staff import Staff
from models.user import Users

staff_bp = Blueprint('staff', __name__)

@staff_bp.route('/staff', methods=['GET'])
def list_staff():
    staffs = Staff.query.all()
    result = []
    for s in staffs:
        user = Users.query.get(s.user_id)
        result.append({
            'id': s.id,
            'user_id': s.user_id,
            'name': user.name if user else None,
            'email': user.email if user else None,
            'phone': s.phone,
            'is_active': s.is_active,
            'is_available': s.is_available
        })
    return jsonify(result)

@staff_bp.route('/staff/available', methods=['GET'])
def available_staff():
    staffs = Staff.query.filter_by(is_active=True, is_available=True).all()
    result = []
    for s in staffs:
        user = Users.query.get(s.user_id)
        result.append({
            'id': s.id,
            'user_id': s.user_id,
            'name': user.name if user else None,
            'email': user.email if user else None,
            'phone': s.phone,
            'is_active': s.is_active,
            'is_available': s.is_available
        })
    return jsonify(result)


@staff_bp.route('/staff', methods=['POST'])
@jwt_required()
def create_staff():
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'message': 'admin required'}), 403
    data = request.get_json() or {}
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')
    if not name or not email or not password:
        return jsonify({'message': 'name, email and password required'}), 400
    if Users.query.filter_by(email=email).first():
        return jsonify({'message': 'email already exists'}), 400
    u = Users(name=name, email=email, role='staff')
    u.set_password(password)
    db.session.add(u)
    db.session.flush()
    s = Staff(user_id=u.id, phone=phone, is_active=True, is_available=True)
    db.session.add(s)
    db.session.commit()
    return jsonify({'user': u.to_dict(), 'staff': s.to_dict()}), 201


@staff_bp.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'message': 'admin required'}), 403
    users = Users.query.all()
    out = []
    for u in users:
        out.append({'id': u.id, 'name': u.name, 'email': u.email, 'role': u.role})
    return jsonify(out)


@staff_bp.route('/staff/<int:staff_id>', methods=['PUT'])
@jwt_required()
def update_staff(staff_id):
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'message': 'admin required'}), 403
    data = request.get_json() or {}
    s = Staff.query.get(staff_id)
    if not s:
        return jsonify({'message': 'staff not found'}), 404
    user = Users.query.get(s.user_id)
    if not user:
        return jsonify({'message': 'linked user not found'}), 404
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')
    if name:
        user.name = name
    if email:
        # ensure email not used by another user
        existing = Users.query.filter(Users.email == email, Users.id != user.id).first()
        if existing:
            return jsonify({'message': 'email already exists'}), 400
        user.email = email
    if password:
        user.set_password(password)
    if phone is not None:
        s.phone = phone
    db.session.commit()
    return jsonify({'user': user.to_dict(), 'staff': s.to_dict()})


@staff_bp.route('/staff/<int:staff_id>', methods=['DELETE'])
@jwt_required()
def delete_staff(staff_id):
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'message': 'admin required'}), 403
    s = Staff.query.get(staff_id)
    if not s:
        return jsonify({'message': 'staff not found'}), 404
    user = Users.query.get(s.user_id)
    # delete staff and user
    try:
        if s:
            db.session.delete(s)
        if user:
            db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'failed to delete', 'error': str(e)}), 500


@staff_bp.route('/staff/me', methods=['POST'])
@jwt_required()
def create_my_staff_profile():
    # Allows a logged-in user with role 'staff' to create their Staff profile if missing
    claims = get_jwt()
    if claims.get('role') != 'staff':
        return jsonify({'message': 'staff role required'}), 403
    uid = get_jwt_identity()
    try:
        user_id = int(uid)
    except Exception:
        return jsonify({'message': 'invalid token identity'}), 400

    # If a Staff row already exists, return it
    existing = Staff.query.filter_by(user_id=user_id).first()
    if existing:
        return jsonify({'staff': existing.to_dict()}), 200

    # create staff row
    data = request.get_json() or {}
    phone = data.get('phone')
    s = Staff(user_id=user_id, phone=phone, is_active=True, is_available=True)
    db.session.add(s)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'failed to create staff profile', 'error': str(e)}), 500

    return jsonify({'staff': s.to_dict()}), 201


@staff_bp.route('/staff/me', methods=['GET'])
@jwt_required()
def get_my_staff_profile():
    claims = get_jwt()
    if claims.get('role') != 'staff':
        return jsonify({'message': 'staff role required'}), 403
    uid = get_jwt_identity()
    try:
        user_id = int(uid)
    except Exception:
        return jsonify({'message': 'invalid token identity'}), 400
    s = Staff.query.filter_by(user_id=user_id).first()
    if not s:
        return jsonify({'message': 'staff profile not found'}), 404
    return jsonify(s.to_dict())


@staff_bp.route('/staff/me', methods=['PUT'])
@jwt_required()
def update_my_staff_profile():
    claims = get_jwt()
    if claims.get('role') != 'staff':
        return jsonify({'message': 'staff role required'}), 403
    uid = get_jwt_identity()
    try:
        user_id = int(uid)
    except Exception:
        return jsonify({'message': 'invalid token identity'}), 400

    s = Staff.query.filter_by(user_id=user_id).first()
    if not s:
        return jsonify({'message': 'staff profile not found'}), 404

    data = request.get_json() or {}
    phone = data.get('phone')
    is_available = data.get('is_available')
    if phone is not None:
        s.phone = phone
    if is_available is not None:
        # accept booleans or strings
        if isinstance(is_available, str):
            s.is_available = is_available.lower() in ('1','true','yes')
        else:
            s.is_available = bool(is_available)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'failed to update staff profile', 'error': str(e)}), 500

    return jsonify({'staff': s.to_dict()})
