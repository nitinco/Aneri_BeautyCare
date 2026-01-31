from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt
from extensions import db
from models import Category, SubCategory, Service, Package, PackageDetail
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
import os
import uuid
from werkzeug.utils import secure_filename

svc_bp = Blueprint('service', __name__)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


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


@svc_bp.route('/subcategories', methods=['GET'])
def list_subcategories():
    subcats = SubCategory.query.all()
    return jsonify([sc.to_dict() for sc in subcats])


@svc_bp.route('/subcategories', methods=['POST'])
@jwt_required()
def create_subcategory():
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    data = request.get_json() or {}
    name = data.get('name')
    category_id = data.get('category_id')
    description = data.get('description')
    if not name or not category_id:
        return jsonify({'message': 'name and category_id required'}), 400
    if not Category.query.get(category_id):
        return jsonify({'message': 'category not found'}), 400
    sc = SubCategory(name=name, category_id=category_id, description=description)
    db.session.add(sc)
    db.session.commit()
    return jsonify(sc.to_dict()), 201


@svc_bp.route('/subcategories/<int:sc_id>', methods=['PUT'])
@jwt_required()
def update_subcategory(sc_id):
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    sc = SubCategory.query.get(sc_id)
    if not sc:
        return jsonify({'message': 'subcategory not found'}), 404
    data = request.get_json() or {}
    sc.name = data.get('name', sc.name)
    sc.category_id = data.get('category_id', sc.category_id)
    sc.description = data.get('description', sc.description)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'message': 'failed to update'}), 500
    return jsonify(sc.to_dict()), 200


@svc_bp.route('/subcategories/<int:sc_id>', methods=['DELETE'])
@jwt_required()
def delete_subcategory(sc_id):
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    sc = SubCategory.query.get(sc_id)
    if not sc:
        return jsonify({'message': 'subcategory not found'}), 404
    try:
        db.session.delete(sc)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'message': 'failed to delete'}), 500
    return jsonify({'message': 'deleted'}), 200


@svc_bp.route('/services', methods=['GET'])
def list_services():
    from models import Offer
    services = Service.query.all()
    out = []
    for s in services:
        d = s.to_dict()
        
        # Get applicable offers for this service
        offers = Offer.query.filter(
            ((Offer.service_id == s.id) | (Offer.service_id.is_(None))) &
            (Offer.is_active == True)
        ).all()
        
        # Filter valid offers
        valid_offers = [o for o in offers if o.is_valid()]
        d['offers'] = [o.to_dict() for o in valid_offers]
        
        # Calculate discounted price if any offer applies
        if valid_offers:
            # Find the best offer (highest discount)
            best_offer = max(valid_offers, key=lambda o: o.discount_percent)
            d['discounted_price'] = float(s.price) * (1 - best_offer.discount_percent / 100)
            d['applied_offer'] = best_offer.to_dict()
        else:
            d['discounted_price'] = None
            d['applied_offer'] = None
            
        out.append(d)
    return jsonify(out)


@svc_bp.route('/services', methods=['POST'])
@jwt_required()
def create_service():
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    
    # Handle both form data and JSON
    if request.content_type and 'multipart/form-data' in request.content_type:
        name = request.form.get('name')
        price = request.form.get('price', 0.0)
        duration = request.form.get('duration_mins', 30)
        description = request.form.get('description')
        subcategory_id = request.form.get('subcategory_id')
        service_type = request.form.get('service_type', 'in-center')
        image_file = request.files.get('image')
    else:
        data = request.get_json() or {}
        name = data.get('name')
        price = data.get('price', 0.0)
        duration = data.get('duration_mins', 30)
        description = data.get('description')
        subcategory_id = data.get('subcategory_id')
        service_type = data.get('service_type', 'in-center')
        image_file = None

    if not name:
        return jsonify({'message': 'name required'}), 400

    # Handle image upload
    image_path = None
    if image_file and allowed_file(image_file.filename):
        filename = secure_filename(image_file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        image_file.save(upload_path)
        image_path = f"uploads/{unique_filename}"

    svc = Service(name=name, price=price, duration_mins=duration, description=description,
                  subcategory_id=subcategory_id, service_type=service_type,
                  image=image_path)
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
    details = data.get('details', [])  # list of {service_id, no_of_sitting}
    is_active = data.get('is_active', True)

    if not name:
        return jsonify({'message': 'name required'}), 400

    pkg = Package(name=name, price=price, description=description, is_active=is_active)
    db.session.add(pkg)
    db.session.flush()

    for d in details:
        sd = PackageDetail(package_id=pkg.id, service_id=d.get('service_id'), no_of_sitting=d.get('no_of_sitting', 1))
        db.session.add(sd)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'failed to create package'}), 500

    return jsonify(pkg.to_dict()), 201


@svc_bp.route('/packages/<int:package_id>', methods=['GET'])
def get_package(package_id):
    pkg = Package.query.get(package_id)
    if not pkg:
        return jsonify({'message': 'package not found'}), 404
    return jsonify(pkg.to_dict())


@svc_bp.route('/packages/<int:package_id>', methods=['PUT'])
@jwt_required()
def update_package(package_id):
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403

    pkg = Package.query.get(package_id)
    if not pkg:
        return jsonify({'message': 'package not found'}), 404

    data = request.get_json() or {}
    pkg.name = data.get('name', pkg.name)
    pkg.price = data.get('price', pkg.price)
    pkg.description = data.get('description', pkg.description)
    pkg.is_active = data.get('is_active', pkg.is_active)

    # Update package details
    details = data.get('details', [])
    if details:
        # Delete existing details
        PackageDetail.query.filter_by(package_id=package_id).delete()

        # Add new details
        for d in details:
            sd = PackageDetail(package_id=package_id, service_id=d.get('service_id'), no_of_sitting=d.get('no_of_sitting', 1))
            db.session.add(sd)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'message': 'failed to update package'}), 500

    return jsonify(pkg.to_dict())


@svc_bp.route('/packages/<int:package_id>', methods=['DELETE'])
@jwt_required()
def delete_package(package_id):
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403

    pkg = Package.query.get(package_id)
    if not pkg:
        return jsonify({'message': 'package not found'}), 404

    try:
        db.session.delete(pkg)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'message': 'failed to delete package'}), 500

    return jsonify({'message': 'package deleted'}), 200


@svc_bp.route('/services/<int:svc_id>', methods=['PUT'])
@jwt_required()
def update_service(svc_id):
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    svc = Service.query.get(svc_id)
    if not svc:
        return jsonify({'message': 'service not found'}), 404
    
    # Handle both form data and JSON
    if request.content_type and 'multipart/form-data' in request.content_type:
        svc.name = request.form.get('name', svc.name)
        svc.description = request.form.get('description', svc.description)
        svc.price = request.form.get('price', svc.price)
        svc.duration_mins = request.form.get('duration_mins', svc.duration_mins)
        svc.subcategory_id = request.form.get('subcategory_id', svc.subcategory_id)
        svc.service_type = request.form.get('service_type', svc.service_type)
        image_file = request.files.get('image')
    else:
        data = request.get_json() or {}
        svc.name = data.get('name', svc.name)
        svc.description = data.get('description', svc.description)
        svc.price = data.get('price', svc.price)
        svc.duration_mins = data.get('duration_mins', svc.duration_mins)
        svc.subcategory_id = data.get('subcategory_id', svc.subcategory_id)
        svc.service_type = data.get('service_type', svc.service_type)
        image_file = None

    # Handle image upload
    if image_file and allowed_file(image_file.filename):
        # Delete old image if exists
        if svc.image:
            old_image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(svc.image))
            if os.path.exists(old_image_path):
                os.remove(old_image_path)
        
        filename = secure_filename(image_file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        image_file.save(upload_path)
        svc.image = f"uploads/{unique_filename}"

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
