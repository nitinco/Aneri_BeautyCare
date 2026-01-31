from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt
from extensions import db
from models import Brand, Product, ProductDetail, Supplier, Stock
import os
import uuid
from werkzeug.utils import secure_filename

prod_bp = Blueprint('product', __name__)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def admin_required():
    claims = get_jwt()
    return claims.get('role') == 'admin'


@prod_bp.route('/brands', methods=['GET'])
def list_brands():
    return jsonify([b.to_dict() for b in Brand.query.all()])


@prod_bp.route('/suppliers', methods=['GET'])
def list_suppliers():
    return jsonify([s.to_dict() for s in Supplier.query.all()])


@prod_bp.route('/suppliers', methods=['POST'])
@jwt_required()
def create_supplier():
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    data = request.get_json() or {}
    s = Supplier(name=data.get('name'), contact=data.get('contact'), address=data.get('address'))
    db.session.add(s)
    db.session.commit()
    return jsonify(s.to_dict()), 201


@prod_bp.route('/suppliers/<int:supplier_id>', methods=['PUT'])
@jwt_required()
def update_supplier(supplier_id):
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    s = Supplier.query.get(supplier_id)
    if not s:
        return jsonify({'message': 'not found'}), 404
    data = request.get_json() or {}
    s.name = data.get('name', s.name)
    s.contact = data.get('contact', s.contact)
    s.address = data.get('address', s.address)
    db.session.commit()
    return jsonify(s.to_dict())


@prod_bp.route('/suppliers/<int:supplier_id>', methods=['DELETE'])
@jwt_required()
def delete_supplier(supplier_id):
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    s = Supplier.query.get(supplier_id)
    if not s:
        return jsonify({'message': 'not found'}), 404
    # optional: prevent delete if stocks exist
    if s.stocks and len(s.stocks) > 0:
        return jsonify({'message': 'supplier has associated stock entries'}), 400
    db.session.delete(s)
    db.session.commit()
    return jsonify({'ok': True})


@prod_bp.route('/brands', methods=['POST'])
@jwt_required()
def create_brand():
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    data = request.get_json() or {}
    b = Brand(name=data.get('name'), description=data.get('description'))
    db.session.add(b)
    db.session.commit()
    return jsonify(b.to_dict()), 201


@prod_bp.route('/brands/<int:brand_id>', methods=['PUT'])
@jwt_required()
def update_brand(brand_id):
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    b = Brand.query.get(brand_id)
    if not b:
        return jsonify({'message': 'not found'}), 404
    data = request.get_json() or {}
    b.name = data.get('name', b.name)
    b.description = data.get('description', b.description)
    db.session.commit()
    return jsonify(b.to_dict())


@prod_bp.route('/brands/<int:brand_id>', methods=['DELETE'])
@jwt_required()
def delete_brand(brand_id):
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    b = Brand.query.get(brand_id)
    if not b:
        return jsonify({'message': 'not found'}), 404
    # optional: prevent delete if products exist
    if b.products and len(b.products) > 0:
        return jsonify({'message': 'brand has associated products'}), 400
    db.session.delete(b)
    db.session.commit()
    return jsonify({'ok': True})


@prod_bp.route('/products', methods=['GET'])
def list_products():
    from models import Offer
    prods = Product.query.all()
    out = []
    for p in prods:
        d = p.to_dict()
        try:
            d['brand_name'] = p.brand.name if p.brand else None
        except Exception:
            d['brand_name'] = None
        
        # Get applicable offers for this product
        offers = Offer.query.filter(
            ((Offer.product_id == p.id) | (Offer.product_id.is_(None))) &
            (Offer.is_active == True)
        ).all()
        
        # Filter valid offers
        valid_offers = [o for o in offers if o.is_valid()]
        d['offers'] = [o.to_dict() for o in valid_offers]
        
        # Calculate discounted price if any offer applies
        if valid_offers:
            # Find the best offer (highest discount)
            best_offer = max(valid_offers, key=lambda o: o.discount_percent)
            d['discounted_price'] = float(p.price) * (1 - best_offer.discount_percent / 100)
            d['applied_offer'] = best_offer.to_dict()
        else:
            d['discounted_price'] = None
            d['applied_offer'] = None
            
        out.append(d)
    return jsonify(out)


@prod_bp.route('/products', methods=['POST'])
@jwt_required()
def create_product():
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    
    # Handle both form data and JSON
    if request.content_type and 'multipart/form-data' in request.content_type:
        name = request.form.get('name')
        brand_id = request.form.get('brand_id')
        sku = request.form.get('sku')
        price = request.form.get('price', 0)
        image_file = request.files.get('image')
    else:
        data = request.get_json() or {}
        name = data.get('name')
        brand_id = data.get('brand_id')
        sku = data.get('sku')
        price = data.get('price', 0)
        image_file = None

    if not name:
        return jsonify({'message': 'name is required'}), 400

    # Handle image upload first
    image_path = None
    if image_file and allowed_file(image_file.filename):
        filename = secure_filename(image_file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        image_file.save(upload_path)
        image_path = f"uploads/{unique_filename}"

    # Create the product
    p = Product(name=name, brand_id=brand_id, sku=sku, price=price, image=image_path)
    db.session.add(p)
    db.session.commit()
    return jsonify(p.to_dict()), 201


@prod_bp.route('/products/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    p = Product.query.get(product_id)
    if not p:
        return jsonify({'message': 'not found'}), 404
    
    # Handle both form data and JSON
    if request.content_type and 'multipart/form-data' in request.content_type:
        p.name = request.form.get('name', p.name)
        p.brand_id = request.form.get('brand_id', p.brand_id)
        p.sku = request.form.get('sku', p.sku)
        p.price = request.form.get('price', p.price)
        image_file = request.files.get('image')
    else:
        data = request.get_json() or {}
        p.name = data.get('name', p.name)
        p.brand_id = data.get('brand_id', p.brand_id)
        p.sku = data.get('sku', p.sku)
        p.price = data.get('price', p.price)
        image_file = None

    # Handle image upload
    if image_file and allowed_file(image_file.filename):
        # Delete old image if exists
        if p.image:
            old_image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(p.image))
            if os.path.exists(old_image_path):
                os.remove(old_image_path)
        
        filename = secure_filename(image_file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        image_file.save(upload_path)
        p.image = f"uploads/{unique_filename}"

    db.session.commit()
    return jsonify(p.to_dict())


@prod_bp.route('/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    p = Product.query.get(product_id)
    if not p:
        return jsonify({'message': 'not found'}), 404
    db.session.delete(p)
    db.session.commit()
    return jsonify({'ok': True})


@prod_bp.route('/stock', methods=['GET'])
@jwt_required()
def list_stock():
    stocks = Stock.query.all()
    out = []
    for s in stocks:
        d = s.to_dict()
        try:
            d['product_name'] = s.product.name if s.product else None
        except Exception:
            d['product_name'] = None
        try:
            d['supplier_name'] = s.supplier.name if s.supplier else None
        except Exception:
            d['supplier_name'] = None
        try:
            d['updated_at'] = s.last_updated.strftime('%Y-%m-%d %H:%M') if getattr(s, 'last_updated', None) else None
        except Exception:
            d['updated_at'] = None
        out.append(d)
    return jsonify(out)


@prod_bp.route('/stock', methods=['POST'])
@jwt_required()
def add_stock():
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    data = request.get_json() or {}
    s = Stock(product_id=data.get('product_id'), supplier_id=data.get('supplier_id'), quantity=data.get('quantity',0), reorder_level=data.get('reorder_level',5))
    db.session.add(s)
    db.session.commit()
    return jsonify(s.to_dict()), 201


@prod_bp.route('/stock/low', methods=['GET'])
@jwt_required()
def low_stock():
    # simple low-stock alert
    low = Stock.query.filter(Stock.quantity <= Stock.reorder_level).all()
    return jsonify([s.to_dict() for s in low])


@prod_bp.route('/stock/<int:stock_id>', methods=['PUT'])
@jwt_required()
def update_stock(stock_id):
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    s = Stock.query.get(stock_id)
    if not s:
        return jsonify({'message': 'not found'}), 404
    data = request.get_json() or {}
    s.product_id = data.get('product_id', s.product_id)
    s.supplier_id = data.get('supplier_id', s.supplier_id)
    try:
        s.quantity = int(data.get('quantity', s.quantity))
    except Exception:
        pass
    try:
        s.reorder_level = int(data.get('reorder_level', s.reorder_level))
    except Exception:
        pass
    db.session.commit()
    d = s.to_dict()
    try:
        d['product_name'] = s.product.name if s.product else None
    except Exception:
        d['product_name'] = None
    try:
        d['supplier_name'] = s.supplier.name if s.supplier else None
    except Exception:
        d['supplier_name'] = None
    try:
        d['updated_at'] = s.last_updated.strftime('%Y-%m-%d %H:%M') if getattr(s, 'last_updated', None) else None
    except Exception:
        d['updated_at'] = None
    return jsonify(d)


@prod_bp.route('/stock/<int:stock_id>', methods=['DELETE'])
@jwt_required()
def delete_stock(stock_id):
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    s = Stock.query.get(stock_id)
    if not s:
        return jsonify({'message': 'not found'}), 404
    db.session.delete(s)
    db.session.commit()
    return jsonify({'ok': True})
