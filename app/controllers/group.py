from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import Group, GroupMember, User

group_bp = Blueprint('group', __name__)


@group_bp.route('/group/create', methods=['POST'])
@jwt_required()
def create_group():
    data = request.get_json()
    group_name = data.get('group_name')
    raw_identity = get_jwt_identity()
    try:
        user_id = int(raw_identity)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid token identity'}), 401
    if not group_name:
        return jsonify({'error': 'group_name required'}), 400
    group = Group(group_name=group_name, user_id=user_id)
    db.session.add(group)
    db.session.commit()
    return jsonify({'message': 'Group created', 'group_id': group.group_id}), 201

# Add member to group (organizer only)
@group_bp.route('/group/<int:group_id>/add_member', methods=['POST'])
@jwt_required()
def add_member(group_id):
    # organizer verified by decorator
    data = request.get_json()
    new_user_id = data.get('user_id')
    if not new_user_id:
        return jsonify({'error': 'user_id required'}), 400
    if GroupMember.query.filter_by(group_id=group_id, user_id=new_user_id).first():
        return jsonify({'error': 'User already in group'}), 400
    member = GroupMember(group_id=group_id, user_id=new_user_id, role='member')
    db.session.add(member)
    db.session.commit()
    return jsonify({'message': 'Member added', 'group_member_id': member.gm_id}), 201

# Remove member from group (organizer only)
@group_bp.route('/group/<int:group_id>/remove_member', methods=['POST'])
@jwt_required()
def remove_member(group_id):
    # organizer verified by decorator
    data = request.get_json()
    remove_user_id = data.get('user_id')
    if not remove_user_id:
        return jsonify({'error': 'user_id required'}), 400
    member = GroupMember.query.filter_by(group_id=group_id, user_id=remove_user_id).first()
    if not member:
        return jsonify({'error': 'User not in group'}), 404
    db.session.delete(member)
    db.session.commit()
    return jsonify({'message': 'Member removed'}), 200

# View all members in a group
@group_bp.route('/group/<int:group_id>/members', methods=['GET'])
@jwt_required()
def view_members(group_id):
    group = db.session.get(Group, group_id)
    members = GroupMember.query.filter_by(group_id=group_id).all()
    result = [
        {
            'group_member_id': m.gm_id,
            'user_id': m.user_id,
            'role': m.role,
            'email': db.session.get(User, m.user_id).email if db.session.get(User, m.user_id) else None
        } for m in members
    ]
    return jsonify(result), 200
