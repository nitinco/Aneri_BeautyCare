from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from extensions import db
from models import Order

import razorpay
import os

pay_bp = Blueprint('payments', __name__)


@pay_bp.route('/razorpay/create_order', methods=['POST'])
@jwt_required()
def create_razorpay_order():
    data = request.get_json() or {}
    order_id = data.get('order_id')
    if not order_id:
        return jsonify({'message': 'order_id required'}), 400

    order = Order.query.get(order_id)
    if not order:
        return jsonify({'message': 'order not found'}), 404

    key_id = (current_app.config.get('RAZORPAY_KEY_ID') or os.getenv('RAZORPAY_KEY_ID') or '').strip()
    key_secret = (current_app.config.get('RAZORPAY_KEY_SECRET') or os.getenv('RAZORPAY_KEY_SECRET') or '').strip()
    if not key_id or not key_secret:
        return jsonify({'message': 'Razorpay not configured'}), 503

    client = razorpay.Client(auth=(key_id, key_secret))
    amount = int(round((order.total_amount or 0) * 100))
    payload = {
        'amount': amount,
        'currency': 'INR',
        'receipt': f'order_{order.id}',
        'payment_capture': 1
    }
    try:
        rp_order = client.order.create(data=payload)
    except Exception as e:
        return jsonify({'message': 'failed to create razorpay order', 'error': str(e)}), 500

    return jsonify({'key_id': key_id, 'razorpay_order': rp_order, 'order_id': order.id})


@pay_bp.route('/razorpay/verify', methods=['POST'])
@jwt_required()
def verify_payment():
    data = request.get_json() or {}
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_signature = data.get('razorpay_signature')
    local_order_id = data.get('order_id')

    if not (razorpay_order_id and razorpay_payment_id and razorpay_signature and local_order_id):
        return jsonify({'message': 'missing parameters'}), 400

    key_id = (current_app.config.get('RAZORPAY_KEY_ID') or os.getenv('RAZORPAY_KEY_ID') or '').strip()
    key_secret = (current_app.config.get('RAZORPAY_KEY_SECRET') or os.getenv('RAZORPAY_KEY_SECRET') or '').strip()
    if not key_id or not key_secret:
        return jsonify({'message': 'Razorpay not configured'}), 503

    client = razorpay.Client(auth=(key_id, key_secret))
    params = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature
    }
    try:
        client.utility.verify_payment_signature(params)
    except Exception as e:
        return jsonify({'message': 'signature verification failed', 'error': str(e)}), 400

    # mark order as paid
    order = Order.query.get(local_order_id)
    if not order:
        return jsonify({'message': 'order not found'}), 404
    order.status = 'paid'
    db.session.commit()

    return jsonify({'message': 'payment verified', 'order': order.to_dict()})
