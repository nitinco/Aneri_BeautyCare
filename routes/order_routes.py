from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import db
from models import Cart, CartItem, Order, OrderItem, Product, Customer

order_bp = Blueprint('order', __name__)


@order_bp.route('/orders', methods=['GET'])
@jwt_required()
def list_orders():
    claims = get_jwt()
    # allow admin or staff to view all orders
    if claims.get('role') not in ('admin', 'staff'):
        return jsonify({'message': 'forbidden'}), 403
    orders = Order.query.order_by(Order.created_at.desc()).all()
    out = []
    for o in orders:
        d = o.to_dict()
        # attach customer name if available
        try:
            cust = Customer.query.get(o.customer_id)
            if cust and getattr(cust, 'user', None):
                d['customer_name'] = cust.user.name
        except Exception:
            pass
        # created_at already in to_dict
        out.append(d)
    return jsonify(out)


@order_bp.route('/orders/my', methods=['GET'])
@jwt_required()
def my_orders():
    uid = get_jwt_identity()
    try:
        user_id = int(uid)
    except Exception:
        return jsonify({'message': 'invalid token identity'}), 400
    cust = Customer.query.filter_by(user_id=user_id).first()
    if not cust:
        return jsonify([])
    orders = Order.query.filter_by(customer_id=cust.id).order_by(Order.created_at.desc()).all()
    out = []
    for o in orders:
        d = o.to_dict()
        d['customer_name'] = cust.user.name if getattr(cust, 'user', None) else None
        out.append(d)
    return jsonify(out)


@order_bp.route('/cart', methods=['POST'])
@jwt_required()
def add_to_cart():
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    customer_id = data.get('customer_id')
    product_id = data.get('product_id')
    qty = int(data.get('quantity', 1))
    cart = Cart.query.filter_by(customer_id=customer_id).first()
    if not cart:
        cart = Cart(customer_id=customer_id)
        db.session.add(cart)
        db.session.flush()
    item = CartItem(cart_id=cart.id, product_id=product_id, quantity=qty)
    db.session.add(item)
    db.session.commit()
    return jsonify(cart.to_dict()), 201


@order_bp.route('/cart/<int:cart_id>', methods=['GET'])
@jwt_required()
def view_cart(cart_id):
    cart = Cart.query.get(cart_id)
    if not cart:
        return jsonify({'message': 'not found'}), 404
    return jsonify(cart.to_dict())


@order_bp.route('/orders', methods=['POST'])
@jwt_required()
def create_order():
    data = request.get_json() or {}
    customer_id = data.get('customer_id')
    cart_id = data.get('cart_id')
    cart = Cart.query.get(cart_id)
    if not cart:
        return jsonify({'message': 'cart not found'}), 404
    total = 0
    for it in cart.items:
        prod = Product.query.get(it.product_id)
        price = float(prod.price) if prod else 0
        total += price * it.quantity
    order = Order(customer_id=customer_id, cart_id=cart_id, total_amount=total, status='pending')
    db.session.add(order)
    db.session.flush()
    for it in cart.items:
        prod = Product.query.get(it.product_id)
        oi = OrderItem(order_id=order.id, product_id=it.product_id, quantity=it.quantity, unit_price=(prod.price if prod else 0))
        db.session.add(oi)
    db.session.commit()
    return jsonify(order.to_dict()), 201


@order_bp.route('/orders/<int:order_id>/status', methods=['PUT'])
@jwt_required()
def update_order_status(order_id):
    claims = get_jwt()
    # allow admin or staff to update
    if claims.get('role') not in ('admin', 'staff'):
        return jsonify({'message': 'forbidden'}), 403
    data = request.get_json() or {}
    status = data.get('status')
    if status not in ('pending', 'dispatched', 'delivered'):
        return jsonify({'message': 'invalid status'}), 400
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'message': 'not found'}), 404
    order.status = status
    db.session.commit()
    return jsonify(order.to_dict())
