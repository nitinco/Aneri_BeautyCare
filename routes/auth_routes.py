from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
import datetime
from sqlalchemy.exc import IntegrityError

from extensions import db
from models.user import Users
from models import Customer


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"message": "JSON body required"}), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "`email` and `password` are required"}), 400

    user = Users.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"message": "Invalid credentials"}), 401

    additional_claims = {"role": user.role}
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims=additional_claims,
        expires_delta=datetime.timedelta(hours=24)
    )

    return jsonify({
        "token": access_token,
        "user": user.to_dict()
    }), 200


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"message": "JSON body required"}), 400

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "customer")

    if not name or not email or not password:
        return jsonify({"message": "Missing fields"}), 400

    if Users.query.filter_by(email=email).first():
        return jsonify({"message": "User already exists"}), 400

    user = Users(name=name, email=email, role=role)
    user.set_password(password)

    db.session.add(user)
    try:
        # create customer profile for role 'customer' within same transaction
        db.session.flush()
        if role == 'customer':
            cust = Customer(user_id=user.id)
            db.session.add(cust)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "User already exists"}), 400
    except Exception:
        db.session.rollback()
        return jsonify({"message": "Failed to register user"}), 500

    return jsonify({
        "message": "User registered successfully",
        "user": user.to_dict()
    }), 201


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    user = Users.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    return jsonify({'user': user.to_dict()}), 200


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = Users.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json() or {}
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    # normalize email if provided
    if email:
        norm_email = email.strip().lower()
    else:
        norm_email = None

    if norm_email and norm_email != (user.email or '').strip().lower():
        # check uniqueness
        existing = Users.query.filter(Users.email == norm_email, Users.id != user.id).first()
        if existing:
            return jsonify({"message": "Email already in use"}), 400
        user.email = norm_email

    if name:
        user.name = name

    if password:
        try:
            user.set_password(password)
        except Exception:
            return jsonify({"message": "Failed to set password"}), 500

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Email already in use"}), 400
    except Exception:
        db.session.rollback()
        return jsonify({"message": "Failed to update profile"}), 500

    return jsonify({'user': user.to_dict()}), 200
