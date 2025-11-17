from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models import User
from flask_jwt_extended import create_access_token, jwt_required

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    email = data.get("email"); password = data.get("password")
    phone_number = data.get("phone_number")
    if not email or not password:
        return jsonify(msg="email and password required"), 400
    if User.query.filter_by(email=email).first():
        return jsonify(msg="email exists"), 400
    user = User(email=email, first_name=data.get("first_name"), last_name=data.get("last_name"), phone_number=phone_number)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify(msg="created", user_id=user.user_id), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    email = data.get("email"); password = data.get("password")
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify(msg="bad credentials"), 401
    token = create_access_token(identity=str(user.user_id))
    return jsonify(access_token=token)

@auth_bp.route("/user_by_email", methods=["GET"])
@jwt_required()
def user_by_email():
    email = request.args.get("email")
    user = None
    if email:
        user = User.query.filter_by(email=email).first()
    else:
        from flask_jwt_extended import get_jwt_identity
        identity = get_jwt_identity()
        # identity may be user_id (str or int)
        try:
            user_id = int(identity)
            user = User.query.get(user_id)
        except Exception:
            user = None
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user_id": user.user_id, "email": user.email, "first_name": user.first_name, "last_name": user.last_name}), 200
