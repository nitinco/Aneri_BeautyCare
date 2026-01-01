from flask import Blueprint, request, jsonify, send_file, make_response
from flask_jwt_extended import jwt_required, get_jwt
from extensions import db
from models import Bill, BillDetail, Payment
import os
import io
from datetime import datetime

# optional imports
try:
    import razorpay
except Exception:
    razorpay = None
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
except Exception:
    letter = None
    canvas = None

billing_bp = Blueprint('billing', __name__)


def admin_required():
    claims = get_jwt()
    return claims.get('role') == 'admin'


@billing_bp.route('/bills', methods=['GET'])
@jwt_required()
def list_bills():
    bills = Bill.query.all()
    return jsonify([b.to_dict() for b in bills])


@billing_bp.route('/bills', methods=['POST'])
@jwt_required()
def create_bill():
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    data = request.get_json() or {}
    customer_id = data.get('customer_id')
    details = data.get('details', [])
    total = sum([float(d.get('amount', 0)) for d in details])
    bill = Bill(customer_id=customer_id, total_amount=total)
    db.session.add(bill)
    db.session.flush()
    for d in details:
        bd = BillDetail(bill_id=bill.id, service_id=d.get('service_id'), product_id=d.get('product_id'), description=d.get('description'), quantity=d.get('quantity',1), unit_price=d.get('unit_price',0), amount=d.get('amount',0))
        db.session.add(bd)
    db.session.commit()
    return jsonify(bill.to_dict()), 201


@billing_bp.route('/bills/<int:bill_id>', methods=['GET'])
@jwt_required()
def get_bill(bill_id):
    b = Bill.query.get(bill_id)
    if not b:
        return jsonify({'message': 'not found'}), 404
    return jsonify(b.to_dict())


@billing_bp.route('/payments', methods=['POST'])
@jwt_required()
def add_payment():
    data = request.get_json() or {}
    bill_id = data.get('bill_id')
    amount = data.get('amount')
    method = data.get('method')
    provider = data.get('provider')
    # Basic payment record creation. Prefer using /payments/create_order and /payments/verify
    p = Payment(bill_id=bill_id, amount=amount, method=method, provider=provider, status='completed')
    db.session.add(p)
    db.session.commit()
    return jsonify(p.to_dict()), 201


@billing_bp.route('/payments/create_order', methods=['POST'])
@jwt_required()
def create_payment_order():
    data = request.get_json() or {}
    bill_id = data.get('bill_id')
    amount = data.get('amount')
    if not bill_id or not amount:
        return jsonify({'message': 'bill_id and amount required'}), 400
    # Amount expected in rupees; razorpay expects paise
    r_key = os.environ.get('RAZORPAY_KEY_ID')
    r_secret = os.environ.get('RAZORPAY_KEY_SECRET')
    order_info = None
    if razorpay and r_key and r_secret:
        client = razorpay.Client(auth=(r_key, r_secret))
        order = client.order.create({'amount': int(float(amount) * 100), 'currency': 'INR', 'payment_capture': 1})
        order_info = order
    # create local payment record
    p = Payment(bill_id=bill_id, amount=amount, method='razorpay' if order_info else 'local', provider='razorpay' if order_info else 'local', provider_payment_id=(order_info.get('id') if order_info else None), status='created')
    db.session.add(p)
    db.session.commit()
    resp = p.to_dict()
    if order_info:
        resp['order'] = order_info
    return jsonify(resp), 201


@billing_bp.route('/payments/verify', methods=['POST'])
@jwt_required()
def verify_payment():
    data = request.get_json() or {}
    payment_id = data.get('payment_id')
    provider_payment_id = data.get('provider_payment_id')
    signature = data.get('signature')
    p = Payment.query.get(payment_id)
    if not p:
        return jsonify({'message': 'payment not found'}), 404
    # If razorpay client present and signature provided, try verification
    r_key = os.environ.get('RAZORPAY_KEY_ID')
    r_secret = os.environ.get('RAZORPAY_KEY_SECRET')
    verified = False
    if razorpay and r_key and r_secret and signature and provider_payment_id:
        client = razorpay.Client(auth=(r_key, r_secret))
        try:
            client.utility.verify_payment_signature({'razorpay_order_id': p.provider_payment_id or data.get('order_id'), 'razorpay_payment_id': provider_payment_id, 'razorpay_signature': signature})
            verified = True
        except Exception:
            verified = False
    else:
        # fallback: if provider_payment_id present, mark verified
        verified = bool(provider_payment_id)
    p.provider_payment_id = provider_payment_id
    p.status = 'completed' if verified else 'failed'
    db.session.commit()
    return jsonify(p.to_dict())


@billing_bp.route('/webhook/razorpay', methods=['POST'])
def razorpay_webhook():
    payload = request.get_data()
    sig = request.headers.get('X-Razorpay-Signature')
    secret = os.environ.get('RAZORPAY_WEBHOOK_SECRET')
    # verify signature if secret available
    if secret and sig:
        import hmac, hashlib
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, sig):
            return jsonify({'message': 'invalid signature'}), 400
    # process payload minimally
    try:
        ev = request.get_json() or {}
        # example: payment.captured
        ev_name = ev.get('event')
        data = ev.get('payload', {})
        # handle basic events
        if ev_name and 'payment' in ev_name:
            payment_obj = data.get('payment', {}).get('entity')
            if payment_obj:
                provider_id = payment_obj.get('id')
                # try find Payment
                p = Payment.query.filter_by(provider_payment_id=provider_id).first()
                if p:
                    p.status = 'completed' if 'captured' in ev_name or payment_obj.get('status') == 'captured' else p.status
                    db.session.commit()
    except Exception:
        pass
    return jsonify({'ok': True})


@billing_bp.route('/bills/<int:bill_id>/pdf', methods=['GET'])
@jwt_required()
def bill_pdf(bill_id):
    b = Bill.query.get(bill_id)
    if not b:
        return jsonify({'message': 'not found'}), 404
    if canvas and letter:
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        c.setFont('Helvetica', 12)
        c.drawString(50, 750, f"Bill ID: {b.id}")
        c.drawString(50, 735, f"Customer ID: {b.customer_id}")
        c.drawString(50, 720, f"Date: {b.created_at.isoformat()}")
        y = 700
        for d in b.details:
            c.drawString(50, y, f"- {d.description or ''} Qty:{d.quantity} Amount: {float(d.amount)}")
            y -= 15
        c.drawString(50, y-10, f"Total: {float(b.total_amount)}")
        c.showPage()
        c.save()
        buf.seek(0)
        return send_file(buf, mimetype='application/pdf', download_name=f'bill_{b.id}.pdf')
    else:
        return jsonify(b.to_dict())
