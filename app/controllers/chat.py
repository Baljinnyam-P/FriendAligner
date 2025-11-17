from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import ChatMessage, Group, GroupMember, User
from app.utils.authz import require_group_member

chat_bp = Blueprint('chat', __name__)

#Not complete
@chat_bp.route('/chat/<int:group_id>/messages', methods=['GET'])
@jwt_required()
@require_group_member('group_id')
def list_messages(group_id):
    limit = int(request.args.get('limit', 50))
    after_id = request.args.get('after_id')
    q = ChatMessage.query.filter_by(group_id=group_id).order_by(ChatMessage.message_id.desc())
    if after_id:
        q = q.filter(ChatMessage.message_id > int(after_id))
    messages = q.limit(limit).all()
    result = [
        {
            'message_id': m.message_id,
            'user_id': m.user_id,
            'content': m.content,
            'created_at': m.created_at.isoformat(),
            'user_name': f"{m.user.first_name} {m.user.last_name}" if m.user else None
        } for m in reversed(messages)  
    ]
    return jsonify(result), 200

@chat_bp.route('/chat/<int:group_id>/message', methods=['POST'])
@jwt_required()
@require_group_member('group_id')
def post_message(group_id):
    data = request.get_json()
    content = data.get('content')
    if not content:
        return jsonify({'error': 'content required'}), 400
    raw_identity = get_jwt_identity()
    try:
        user_id = int(raw_identity)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid token identity'}), 401
    msg = ChatMessage(group_id=group_id, user_id=user_id, content=content)
    db.session.add(msg)
    db.session.commit()
    return jsonify({'message': 'sent', 'message_id': msg.message_id}), 201
