from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import db
from models import Customer, Area
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_

customer_bp = Blueprint('customer', __name__)


@customer_bp.route('/customers/me', methods=['GET'])
@jwt_required()
def get_my_customer():
    uid = get_jwt_identity()
    try:
        user_id = int(uid)
    except Exception:
        return jsonify({'message': 'invalid token identity'}), 400
    cust = Customer.query.filter_by(user_id=user_id).first()
    if not cust:
        return jsonify({'message': 'Customer profile not found'}), 404
    return jsonify(cust.to_dict())


@customer_bp.route('/customers/me', methods=['POST'])
@jwt_required()
def create_my_customer():
    uid = get_jwt_identity()
    try:
        user_id = int(uid)
    except Exception:
        return jsonify({'message': 'invalid token identity'}), 400
    if Customer.query.filter_by(user_id=user_id).first():
        return jsonify({'message': 'Customer profile already exists'}), 400
    data = request.get_json() or {}
    phone = data.get('phone')
    address = data.get('address')
    area_id = data.get('area_id')
    cust = Customer(user_id=user_id, phone=phone, address=address, area_id=area_id)
    db.session.add(cust)
    db.session.commit()
    return jsonify(cust.to_dict()), 201


@customer_bp.route('/customers/me', methods=['PUT'])
@jwt_required()
def update_my_customer():
    uid = get_jwt_identity()
    try:
        user_id = int(uid)
    except Exception:
        return jsonify({'message': 'invalid token identity'}), 400

    data = request.get_json() or {}
    phone = data.get('phone')
    address = data.get('address')
    area_id = data.get('area_id')

    # validate area_id if provided
    if area_id is not None and area_id != '':
        # allow numeric id, or pincode/name lookup
        matched_area = None
        # try numeric id
        try:
            aid = int(area_id)
            matched_area = Area.query.get(aid)
        except Exception:
            # treat as string: try pincode or name match (case-insensitive)
            val = str(area_id).strip()
            if val:
                matched_area = Area.query.filter(or_(Area.pincode == val, Area.name.ilike(f'%{val}%'))).first()

        if matched_area:
            area_id = matched_area.id
        else:
            # couldn't match: clear area_id (do not block save)
            area_id = None

    cust = Customer.query.filter_by(user_id=user_id).first()
    if not cust:
        # create new profile if missing
        cust = Customer(user_id=user_id, phone=phone, address=address, area_id=area_id)
        db.session.add(cust)
    else:
        if phone is not None:
            cust.phone = phone
        if address is not None:
            cust.address = address
        if area_id is not None:
            cust.area_id = area_id

    try:
        db.session.commit()
    except IntegrityError as ie:
        db.session.rollback()
        return jsonify({'message': 'database integrity error', 'detail': str(ie)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'failed to update customer profile', 'detail': str(e)}), 500

    return jsonify(cust.to_dict()), 200


@customer_bp.route('/customers', methods=['GET'])
@jwt_required()
def list_customers():
    claims = get_jwt()
    if claims.get('role') not in ('admin', 'staff'):
        return jsonify({'message': 'forbidden'}), 403
    customers = Customer.query.all()
    out = []
    for c in customers:
        d = c.to_dict()
        if getattr(c, 'user', None):
            try:
                d['name'] = c.user.name
                d['email'] = c.user.email
            except Exception:
                pass
        out.append(d)
    return jsonify(out)


@customer_bp.route('/areas', methods=['GET'])
def list_areas():
    areas = Area.query.all()
    out = []
    for a in areas:
        out.append({'id': a.id, 'pincode': a.pincode, 'name': a.name, 'city_id': a.city_id})
    return jsonify(out)


@customer_bp.route('/areas/<int:area_id>', methods=['GET'])
def get_area(area_id):
    a = Area.query.get(area_id)
    if not a:
        return jsonify({'message': 'area not found'}), 404
    return jsonify({'id': a.id, 'pincode': a.pincode, 'name': a.name, 'city_id': a.city_id})
