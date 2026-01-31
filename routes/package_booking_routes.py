from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import db
from models import Package, PackageBooking, Customer
import datetime
import razorpay
import os
from flask import current_app

package_booking_bp = Blueprint('package_booking', __name__)


@package_booking_bp.route('/packages/<int:package_id>/book', methods=['POST'])
@jwt_required()
def create_package_booking(package_id):
    """Create a package booking"""
    user_id = get_jwt_identity()
    customer = Customer.query.filter_by(user_id=user_id).first()
    if not customer:
        return jsonify({'message': 'Customer profile not found'}), 404

    package = Package.query.get(package_id)
    if not package:
        return jsonify({'message': 'Package not found'}), 404

    if not package.is_active:
        return jsonify({'message': 'Package is not available for booking'}), 400

    data = request.get_json() or {}
    start_datetime_str = data.get('start_datetime')
    service_type = data.get('service_type', 'salon')
    address = data.get('address')
    pincode = data.get('pincode')
    notes = data.get('notes')

    if not start_datetime_str:
        return jsonify({'message': 'start_datetime is required'}), 400

    try:
        start_datetime = datetime.datetime.fromisoformat(start_datetime_str.replace('Z', '+00:00'))
    except ValueError:
        return jsonify({'message': 'Invalid start_datetime format'}), 400

    # Calculate end time based on package services (simplified - 2 hours per package)
    end_datetime = start_datetime + datetime.timedelta(hours=2)

    # Validate service type requirements
    if service_type == 'home':
        if not address:
            return jsonify({'message': 'Address is required for home service'}), 400
        home_charge = 200.0  # Fixed home service charge
    else:
        home_charge = 0.0
        address = None
        pincode = None

    total_amount = float(package.price) + home_charge

    # Create package booking
    booking = PackageBooking(
        customer_id=customer.id,
        package_id=package_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        address=address,
        pincode=pincode,
        service_type=service_type,
        total_amount=total_amount,
        notes=notes
    )

    db.session.add(booking)
    db.session.commit()

    return jsonify({
        'message': 'Package booking created successfully',
        'booking': booking.to_dict()
    }), 201


@package_booking_bp.route('/bookings', methods=['GET'])
@jwt_required()
def get_my_package_bookings():
    """Get current user's package bookings"""
    user_id = get_jwt_identity()
    customer = Customer.query.filter_by(user_id=user_id).first()
    if not customer:
        return jsonify({'message': 'Customer profile not found'}), 404

    bookings = PackageBooking.query.filter_by(customer_id=customer.id)\
        .order_by(PackageBooking.created_at.desc()).all()

    return jsonify([b.to_dict() for b in bookings])


@package_booking_bp.route('/bookings/<int:booking_id>', methods=['GET'])
@jwt_required()
def get_package_booking(booking_id):
    """Get specific package booking details"""
    user_id = get_jwt_identity()
    customer = Customer.query.filter_by(user_id=user_id).first()
    if not customer:
        return jsonify({'message': 'Customer profile not found'}), 404

    booking = PackageBooking.query.filter_by(id=booking_id, customer_id=customer.id).first()
    if not booking:
        return jsonify({'message': 'Booking not found'}), 404

    return jsonify(booking.to_dict())


@package_booking_bp.route('/bookings/<int:booking_id>/cancel', methods=['PUT'])
@jwt_required()
def cancel_package_booking(booking_id):
    """Cancel a package booking"""
    user_id = get_jwt_identity()
    customer = Customer.query.filter_by(user_id=user_id).first()
    if not customer:
        return jsonify({'message': 'Customer profile not found'}), 404

    booking = PackageBooking.query.filter_by(id=booking_id, customer_id=customer.id).first()
    if not booking:
        return jsonify({'message': 'Booking not found'}), 404

    if booking.status not in ['pending', 'confirmed']:
        return jsonify({'message': 'Cannot cancel booking with current status'}), 400

    booking.status = 'cancelled'
    db.session.commit()

    return jsonify({'message': 'Booking cancelled successfully'})


@package_booking_bp.route('/razorpay/create_order/<int:booking_id>', methods=['POST'])
@jwt_required()
def create_razorpay_order_for_package(booking_id):
    """Create Razorpay order for package booking"""
    user_id = get_jwt_identity()
    customer = Customer.query.filter_by(user_id=user_id).first()
    if not customer:
        return jsonify({'message': 'Customer profile not found'}), 404

    booking = PackageBooking.query.filter_by(id=booking_id, customer_id=customer.id).first()
    if not booking:
        return jsonify({'message': 'Booking not found'}), 404

    if booking.status != 'pending':
        return jsonify({'message': 'Booking is not in pending status'}), 400

    key_id = (current_app.config.get('RAZORPAY_KEY_ID') or os.getenv('RAZORPAY_KEY_ID') or '').strip()
    key_secret = (current_app.config.get('RAZORPAY_KEY_SECRET') or os.getenv('RAZORPAY_KEY_SECRET') or '').strip()
    if not key_id or not key_secret:
        return jsonify({'message': 'Razorpay not configured'}), 503

    client = razorpay.Client(auth=(key_id, key_secret))
    amount = int(round((booking.total_amount or 0) * 100))
    payload = {
        'amount': amount,
        'currency': 'INR',
        'receipt': f'package_booking_{booking.id}',
        'payment_capture': 1
    }

    try:
        rp_order = client.order.create(data=payload)
        booking.razorpay_order_id = rp_order['id']
        db.session.commit()
    except Exception as e:
        return jsonify({'message': 'Failed to create Razorpay order', 'error': str(e)}), 500

    return jsonify({
        'key_id': key_id,
        'razorpay_order': rp_order,
        'booking_id': booking.id
    })


@package_booking_bp.route('/razorpay/verify_payment/<int:booking_id>', methods=['POST'])
@jwt_required()
def verify_package_payment(booking_id):
    """Verify Razorpay payment for package booking"""
    user_id = get_jwt_identity()
    customer = Customer.query.filter_by(user_id=user_id).first()
    if not customer:
        return jsonify({'message': 'Customer profile not found'}), 404

    booking = PackageBooking.query.filter_by(id=booking_id, customer_id=customer.id).first()
    if not booking:
        return jsonify({'message': 'Booking not found'}), 404

    data = request.get_json() or {}
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_signature = data.get('razorpay_signature')

    if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
        return jsonify({'message': 'Missing payment verification data'}), 400

    key_secret = (current_app.config.get('RAZORPAY_KEY_SECRET') or os.getenv('RAZORPAY_KEY_SECRET') or '').strip()
    if not key_secret:
        return jsonify({'message': 'Razorpay not configured'}), 503

    # Verify payment signature
    client = razorpay.Client(auth=(current_app.config.get('RAZORPAY_KEY_ID'), key_secret))

    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        })

        # Update booking status
        booking.razorpay_payment_id = razorpay_payment_id
        booking.status = 'confirmed'
        db.session.commit()

        return jsonify({'message': 'Payment verified successfully'})

    except Exception as e:
        return jsonify({'message': 'Payment verification failed', 'error': str(e)}), 400


# Admin routes for package bookings
@package_booking_bp.route('/admin/bookings', methods=['GET'])
@jwt_required()
def get_all_package_bookings_admin():
    """Get all package bookings for admin"""
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'message': 'Admin access required'}), 403

    bookings = PackageBooking.query.order_by(PackageBooking.created_at.desc()).all()
    result = []
    for booking in bookings:
        booking_dict = booking.to_dict()
        # Add customer name
        if booking.customer and booking.customer.user:
            booking_dict['customer_name'] = booking.customer.user.name
        else:
            booking_dict['customer_name'] = 'N/A'
        result.append(booking_dict)

    return jsonify(result)


@package_booking_bp.route('/admin/bookings/<int:booking_id>', methods=['GET'])
@jwt_required()
def get_package_booking_admin(booking_id):
    """Get specific package booking details for admin"""
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'message': 'Admin access required'}), 403

    booking = PackageBooking.query.get(booking_id)
    if not booking:
        return jsonify({'message': 'Package booking not found'}), 404

    booking_dict = booking.to_dict()
    # Add customer name
    if booking.customer and booking.customer.user:
        booking_dict['customer_name'] = booking.customer.user.name
    else:
        booking_dict['customer_name'] = 'N/A'

    return jsonify(booking_dict)


@package_booking_bp.route('/admin/bookings/<int:booking_id>', methods=['PUT'])
@jwt_required()
def update_package_booking_admin(booking_id):
    """Update package booking status for admin"""
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'message': 'Admin access required'}), 403

    booking = PackageBooking.query.get(booking_id)
    if not booking:
        return jsonify({'message': 'Package booking not found'}), 404

    data = request.get_json() or {}
    new_status = data.get('status')

    if new_status and new_status in ['pending', 'confirmed', 'cancelled', 'completed']:
        booking.status = new_status
        db.session.commit()
        return jsonify({'message': 'Package booking updated successfully'})
    else:
        return jsonify({'message': 'Invalid status'}), 400