from flask import Blueprint, render_template
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Customer, Area
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_

main_bp = Blueprint("main", __name__)

# Public Routes
@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/login")
def login():
    return render_template("login.html")


@main_bp.route("/register")
def register():
    return render_template("register.html")


@main_bp.route('/services')
def services():
    return render_template('services.html')


# Customer Routes
@main_bp.route('/customer/dashboard')
def customer_dashboard():
    return render_template('dashboard.html')


@main_bp.route('/customer/book')
def customer_book():
    return render_template('book.html')


@main_bp.route('/customer/products')
def customer_products():
    return render_template('customer_products.html')


@main_bp.route('/customer/cart')
def customer_cart():
    return render_template('customer_cart.html')


@main_bp.route('/customer/offers')
def customer_offers():
    return render_template('customer_offers.html')


@main_bp.route('/customer/bills')
def customer_bills():
    return render_template('customer_bills.html')


@main_bp.route('/customer/feedback')
def customer_feedback():
    return render_template('customer_feedback.html')


@main_bp.route('/customer/orders')
def customer_orders():
    return render_template('customer_orders.html')


# Admin Routes
@main_bp.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')


@main_bp.route('/admin/services')
def admin_services():
    return render_template('admin_services.html')


@main_bp.route('/admin/customers')
def admin_customers():
    return render_template('admin_customers.html')


@main_bp.route('/admin/appointments')
def admin_appointments():
    return render_template('admin_appointments.html')


@main_bp.route('/admin/stock')
def admin_stock():
    return render_template('admin_stock.html')


@main_bp.route('/admin/users')
def admin_users():
    return render_template('admin_users.html')


@main_bp.route('/admin/staff')
def admin_staff():
    return render_template('admin_staff.html')


@main_bp.route('/admin/brands')
def admin_brands():
    return render_template('admin_brands.html')


@main_bp.route('/admin/products')
def admin_products():
    return render_template('admin_products.html')


@main_bp.route('/admin/orders')
def admin_orders():
    return render_template('admin_orders.html')


@main_bp.route('/admin/bills')
def admin_bills():
    return render_template('admin_bills.html')


@main_bp.route('/admin/offers')
def admin_offers():
    return render_template('admin_offers.html')


@main_bp.route('/admin/complaints')
def admin_complaints():
    return render_template('admin_complaints.html')


@main_bp.route('/admin/delivery')
def admin_delivery():
    return render_template('admin_delivery.html')


# Staff Routes
@main_bp.route('/staff/dashboard')
def staff_dashboard():
    return render_template('staff_dashboard.html')


# Compatibility wrappers for customer API without `/api` prefix
@main_bp.route('/customers/me', methods=['GET'])
@jwt_required()
def customers_me_get():
    uid = get_jwt_identity()
    try:
        user_id = int(uid)
    except Exception:
        return jsonify({'message': 'invalid token identity'}), 400
    cust = Customer.query.filter_by(user_id=user_id).first()
    if not cust:
        return jsonify({'message': 'Customer profile not found'}), 404
    return jsonify(cust.to_dict())


@main_bp.route('/customers/me', methods=['POST'])
@jwt_required()
def customers_me_post():
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

    # resolve area_id: accept numeric id or pincode/name
    if area_id is not None and area_id != '':
        matched_area = None
        try:
            aid = int(area_id)
            matched_area = Area.query.get(aid)
        except Exception:
            val = str(area_id).strip()
            if val:
                matched_area = Area.query.filter(or_(Area.pincode == val, Area.name.ilike(f'%{val}%'))).first()
        if matched_area:
            area_id = matched_area.id
        else:
            area_id = None

    cust = Customer(user_id=user_id, phone=phone, address=address, area_id=area_id)
    db.session.add(cust)
    try:
        db.session.commit()
    except IntegrityError as ie:
        db.session.rollback()
        return jsonify({'message': 'database integrity error', 'detail': str(ie)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'failed to create customer profile', 'detail': str(e)}), 500
    return jsonify(cust.to_dict()), 201


@main_bp.route('/customers/me', methods=['PUT'])
@jwt_required()
def customers_me_put():
    uid = get_jwt_identity()
    try:
        user_id = int(uid)
    except Exception:
        return jsonify({'message': 'invalid token identity'}), 400

    data = request.get_json() or {}
    phone = data.get('phone')
    address = data.get('address')
    area_id = data.get('area_id')

    # resolve area_id: accept numeric id or pincode/name
    if area_id is not None and area_id != '':
        matched_area = None
        try:
            aid = int(area_id)
            matched_area = Area.query.get(aid)
        except Exception:
            val = str(area_id).strip()
            if val:
                matched_area = Area.query.filter(or_(Area.pincode == val, Area.name.ilike(f'%{val}%'))).first()
        if matched_area:
            area_id = matched_area.id
        else:
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

