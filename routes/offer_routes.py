from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from extensions import db
from models import Offer

offer_bp = Blueprint('offer', __name__)


def admin_required():
    claims = get_jwt()
    return claims.get('role') == 'admin'


@offer_bp.route('/offers', methods=['GET'])
def list_offers():
    offers = Offer.query.filter_by(is_active=True).all()
    return jsonify([o.to_dict() for o in offers])


@offer_bp.route('/offers', methods=['POST'])
@jwt_required()
def create_offer():
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    data = request.get_json() or {}
    o = Offer(title=data.get('title'), description=data.get('description'), is_product_offer=data.get('is_product_offer', False), product_id=data.get('product_id'), service_id=data.get('service_id'), discount_percent=data.get('discount_percent',0), start_date=data.get('start_date'), end_date=data.get('end_date'), is_active=data.get('is_active', True))
    db.session.add(o)
    db.session.commit()
    return jsonify(o.to_dict()), 201


@offer_bp.route('/offers/<int:offer_id>', methods=['PUT'])
@jwt_required()
def update_offer(offer_id):
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    data = request.get_json() or {}
    o = Offer.query.get(offer_id)
    if not o:
        return jsonify({'message': 'not found'}), 404
    o.title = data.get('title', o.title)
    o.description = data.get('description', o.description)
    o.is_active = data.get('is_active', o.is_active)
    db.session.commit()
    return jsonify(o.to_dict())


@offer_bp.route('/offers/<int:offer_id>', methods=['DELETE'])
@jwt_required()
def delete_offer(offer_id):
    if not admin_required():
        return jsonify({'message': 'admin role required'}), 403
    o = Offer.query.get(offer_id)
    if not o:
        return jsonify({'message': 'not found'}), 404
    try:
        db.session.delete(o)
        db.session.commit()
        return jsonify({'message': 'deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'failed to delete', 'error': str(e)}), 500
