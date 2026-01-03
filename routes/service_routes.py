from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt
from extensions import db
from models import Category, SubCategory, Service, Package, PackageDetail
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

svc_bp = Blueprint('service', __name__)


def admin_required():
    claims = get_jwt()
    return claims.get('role') == 'admin'


@svc_bp.route('/categories', methods=['GET'])
def list_categories():
    cats = Category.query.all()
    return jsonify([c.to_dict() for c in cats])


@svc_bp.route('/categories', methods=['POST'])
@jwt_required()
def create_category():
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    data = request.get_json() or {}
    name = data.get('name')
    description = data.get('description')
    if not name:
        return jsonify({'message': 'name required'}), 400
    if Category.query.filter_by(name=name).first():
        return jsonify({'message': 'category exists'}), 400
    c = Category(name=name, description=description)
    db.session.add(c)
    db.session.commit()
    return jsonify(c.to_dict()), 201


@svc_bp.route('/categories/<int:cat_id>', methods=['PUT'])
@jwt_required()
def update_category(cat_id):
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    c = Category.query.get(cat_id)
    if not c:
        return jsonify({'message': 'category not found'}), 404
    data = request.get_json() or {}
    c.name = data.get('name', c.name)
    c.description = data.get('description', c.description)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'message': 'failed to update'}), 500
    return jsonify(c.to_dict()), 200


@svc_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
@jwt_required()
def delete_category(cat_id):
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    c = Category.query.get(cat_id)
    if not c:
        return jsonify({'message': 'category not found'}), 404
    try:
        db.session.delete(c)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'message': 'failed to delete'}), 500
    return jsonify({'message': 'deleted'}), 200


@svc_bp.route('/services', methods=['GET'])
def list_services():
    services = Service.query.all()
    return jsonify([s.to_dict() for s in services])


@svc_bp.route('/services', methods=['POST'])
@jwt_required()
def create_service():
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    data = request.get_json() or {}
    name = data.get('name')
    price = data.get('price', 0.0)
    duration = data.get('duration_mins', 30)
    description = data.get('description')
    category_id = data.get('category_id')
    subcategory_id = data.get('subcategory_id')
    service_type = data.get('service_type', 'in-center')

    if not name:
        return jsonify({'message': 'name required'}), 400

    svc = Service(name=name, price=price, duration_mins=duration, description=description,
                  category_id=category_id, subcategory_id=subcategory_id, service_type=service_type)
    db.session.add(svc)
    db.session.commit()
    return jsonify(svc.to_dict()), 201


@svc_bp.route('/packages', methods=['GET'])
def list_packages():
    packs = Package.query.filter_by(is_active=True).all()
    return jsonify([p.to_dict() for p in packs])


@svc_bp.route('/packages', methods=['POST'])
@jwt_required()
def create_package():
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    data = request.get_json() or {}
    name = data.get('name')
    price = data.get('price', 0.0)
    description = data.get('description')
    details = data.get('details', [])  # list of {service_id, quantity}

    if not name:
        return jsonify({'message': 'name required'}), 400

    pkg = Package(name=name, price=price, description=description)
    db.session.add(pkg)
    db.session.flush()

    for d in details:
        sd = PackageDetail(package_id=pkg.id, service_id=d.get('service_id'), quantity=d.get('quantity', 1))
        db.session.add(sd)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'failed to create package'}), 500

    return jsonify(pkg.to_dict()), 201


@svc_bp.route('/services/<int:svc_id>', methods=['PUT'])
@jwt_required()
def update_service(svc_id):
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    svc = Service.query.get(svc_id)
    if not svc:
        return jsonify({'message': 'service not found'}), 404
    data = request.get_json() or {}
    svc.name = data.get('name', svc.name)
    svc.description = data.get('description', svc.description)
    svc.price = data.get('price', svc.price)
    svc.duration_mins = data.get('duration_mins', svc.duration_mins)
    svc.category_id = data.get('category_id', svc.category_id)
    svc.subcategory_id = data.get('subcategory_id', svc.subcategory_id)
    svc.service_type = data.get('service_type', svc.service_type)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'message': 'failed to update'}), 500
    return jsonify(svc.to_dict()), 200


@svc_bp.route('/services/<int:svc_id>', methods=['DELETE'])
@jwt_required()
def delete_service(svc_id):
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    svc = Service.query.get(svc_id)
    if not svc:
        return jsonify({'message': 'service not found'}), 404
    try:
        db.session.delete(svc)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'message': 'failed to delete'}), 500
    return jsonify({'message': 'deleted'}), 200
