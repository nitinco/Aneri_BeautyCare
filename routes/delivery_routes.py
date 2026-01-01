from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from extensions import db
from models import Delivery, Order, Staff

delivery_bp = Blueprint('delivery', __name__)


def admin_required():
    claims = get_jwt()
    return claims.get('role') == 'admin'


@delivery_bp.route('/deliveries', methods=['POST'])
@jwt_required()
def create_delivery():
    # allow admin to create generic delivery; allow staff to create delivery assigned to themselves
    claims = get_jwt()
    data = request.get_json() or {}
    order_id = data.get('order_id')
    if not order_id:
        return jsonify({'message': 'order_id required'}), 400

    # ensure order exists
    ord_obj = Order.query.get(order_id)
    if not ord_obj:
        return jsonify({'message': 'order not found'}), 404

    # Admin path: create delivery unassigned (admin may assign later)
    if claims.get('role') == 'admin':
        d = Delivery(order_id=order_id, status='pending')
        db.session.add(d)
        # mark order as having a pending delivery
        try:
            ord_obj.status = 'pending_delivery'
        except Exception:
            pass
        db.session.commit()
        # include order in response for client refresh
        from models import Customer
        customer = Customer.query.get(ord_obj.customer_id) if ord_obj and ord_obj.customer_id else None
        return jsonify({ 'delivery': d.to_dict(), 'order': ord_obj.to_dict() if ord_obj else None, 'customer': customer.to_dict() if customer else None }), 201

    # Staff path: create delivery and auto-assign to the calling staff
    if claims.get('role') == 'staff':
        uid = get_jwt_identity()
        try:
            user_id = int(uid)
        except Exception:
            return jsonify({'message': 'invalid token identity'}), 400
        st = Staff.query.filter_by(user_id=user_id).first()
        if not st:
            return jsonify({'message': 'staff profile not found'}), 404

        from datetime import datetime
        d = Delivery(order_id=order_id, delivery_staff_id=st.id, status='dispatched', assigned_at=datetime.utcnow())
        db.session.add(d)
        # mark staff as not available
        st.is_available = False
        # update order status -> dispatched (so customer sees it's out)
        try:
            ord_obj.status = 'dispatched'
        except Exception:
            pass
        db.session.commit()
        from models import Customer
        customer = Customer.query.get(ord_obj.customer_id) if ord_obj and ord_obj.customer_id else None
        return jsonify({ 'delivery': d.to_dict(), 'order': ord_obj.to_dict() if ord_obj else None, 'customer': customer.to_dict() if customer else None }), 201

    return jsonify({'message': 'admin or staff role required'}), 403


@delivery_bp.route('/deliveries/<int:delivery_id>/assign', methods=['PUT'])
@jwt_required()
def assign_delivery(delivery_id):
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    data = request.get_json() or {}
    staff_id = data.get('staff_id')
    d = Delivery.query.get(delivery_id)
    if not d:
        return jsonify({'message': 'not found'}), 404
    d.delivery_staff_id = staff_id
    d.status = 'dispatched'
    from datetime import datetime
    d.assigned_at = datetime.utcnow()
    # mark staff as not available
    s = Staff.query.get(staff_id)
    if s:
        s.is_available = False
    # update order status
    try:
        ord = Order.query.get(d.order_id) if d.order_id else None
        if ord:
            ord.status = 'out_for_delivery'
    except Exception:
        pass
    db.session.commit()
    # include related order and customer
    from models import Customer
    order = Order.query.get(d.order_id) if d.order_id else None
    customer = Customer.query.get(order.customer_id) if order and order.customer_id else None
    return jsonify({ 'delivery': d.to_dict(), 'order': order.to_dict() if order else None, 'customer': customer.to_dict() if customer else None })


@delivery_bp.route('/deliveries/<int:delivery_id>/complete', methods=['PUT'])
@jwt_required()
def complete_delivery(delivery_id):
    data = request.get_json() or {}
    d = Delivery.query.get(delivery_id)
    if not d:
        return jsonify({'message': 'not found'}), 404
    d.status = 'delivered'
    from datetime import datetime
    d.delivered_at = datetime.utcnow()
    # free staff
    if d.delivery_staff_id:
        s = Staff.query.get(d.delivery_staff_id)
        if s:
            s.is_available = True
    # update order status to delivered
    try:
        ord = Order.query.get(d.order_id) if d.order_id else None
        if ord:
            ord.status = 'delivered'
    except Exception:
        pass
    db.session.commit()
    # include related order and customer
    from models import Customer
    order = Order.query.get(d.order_id) if d.order_id else None
    customer = Customer.query.get(order.customer_id) if order and order.customer_id else None
    return jsonify({ 'delivery': d.to_dict(), 'order': order.to_dict() if order else None, 'customer': customer.to_dict() if customer else None })


@delivery_bp.route('/deliveries/my', methods=['GET'])
@jwt_required()
def my_deliveries():
    # staff can see deliveries assigned to them
    claims = get_jwt()
    if claims.get('role') != 'staff':
        return jsonify({'message': 'staff role required'}), 403
    uid = get_jwt_identity()
    try:
        user_id = int(uid)
    except Exception:
        return jsonify({'message': 'invalid token identity'}), 400
    st = Staff.query.filter_by(user_id=user_id).first()
    if not st:
        return jsonify({'message': 'staff profile not found'}), 404

    dels = Delivery.query.filter_by(delivery_staff_id=st.id).all()
    out = []
    for d in dels:
        order = Order.query.get(d.order_id) if d.order_id else None
        customer = None
        if order:
            from models import Customer
            customer = Customer.query.get(order.customer_id)
        out.append({
            'delivery': d.to_dict(),
            'order': order.to_dict() if order else None,
            'customer': customer.to_dict() if customer else None
        })
    return jsonify(out)


@delivery_bp.route('/deliveries/<int:delivery_id>/status', methods=['PUT'])
@jwt_required()
def update_delivery_status(delivery_id):
    # allow assigned staff or admin to update status
    data = request.get_json() or {}
    status = data.get('status')
    if not status:
        return jsonify({'message': 'status required'}), 400
    claims = get_jwt()
    uid = get_jwt_identity()
    try:
        user_id = int(uid)
    except Exception:
        return jsonify({'message': 'invalid token identity'}), 400

    d = Delivery.query.get(delivery_id)
    if not d:
        return jsonify({'message': 'not found'}), 404

    # if staff, ensure they are assigned to this delivery
    if claims.get('role') == 'staff':
        st = Staff.query.filter_by(user_id=user_id).first()
        if not st or d.delivery_staff_id != st.id:
            return jsonify({'message': 'not authorized for this delivery'}), 403

    d.status = status
    from datetime import datetime
    if status == 'delivered':
        d.delivered_at = datetime.utcnow()
        # free staff
        if d.delivery_staff_id:
            s = Staff.query.get(d.delivery_staff_id)
            if s:
                s.is_available = True
    if status in ('dispatched', 'out_for_delivery'):
        d.assigned_at = datetime.utcnow()
        if d.delivery_staff_id:
            s = Staff.query.get(d.delivery_staff_id)
            if s:
                s.is_available = False

    # propagate order status changes
    try:
        ord = Order.query.get(d.order_id) if d.order_id else None
        if ord:
            if status == 'delivered':
                ord.status = 'delivered'
            elif status in ('dispatched', 'out_for_delivery'):
                ord.status = 'out_for_delivery'
            elif status in ('pending', 'pending_delivery'):
                ord.status = 'pending_delivery'
    except Exception:
        ord = None

    db.session.commit()

    # include related order and customer for client convenience
    from models import Customer
    customer = None
    if ord and ord.customer_id:
        customer = Customer.query.get(ord.customer_id)

    return jsonify({ 'delivery': d.to_dict(), 'order': ord.to_dict() if ord else None, 'customer': customer.to_dict() if customer else None })
