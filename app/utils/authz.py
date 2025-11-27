from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity
from app.models import User, Group, GroupMember, Event
from app.extensions import db

# Authorization / access control decorators

#Check if user is admin
def require_admin():
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # JWT identity stored as string; normalize to int
            raw_identity = get_jwt_identity()
            try:
                user_id = int(raw_identity)
            except (TypeError, ValueError):
                return jsonify({'error': 'Invalid token identity'}), 401
            user = db.session.get(User, user_id)
            if not user or not user.is_admin:
                return jsonify({'error': 'Admin privileges required'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# Check if user is member of this group
#Ensure current user is a member of the group referenced by param_name in route or JSON body
def require_group_member(param_name='group_id'):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            raw_identity = get_jwt_identity()
            try:
                user_id = int(raw_identity)
            except (TypeError, ValueError):
                return jsonify({'error': 'Invalid token identity'}), 401
            group_id = kwargs.get(param_name)
            if group_id is None:
                data = request.get_json(silent=True) or {}
                group_id = data.get(param_name)
            if group_id is None:
                event_id = kwargs.get('event_id') or data.get('event_id')
                if event_id is not None:
                    event = db.session.get(Event, event_id)
                    if event:
                        group_id = event.group_id
            if group_id is None:
                return jsonify({'error': 'group_id not provided'}), 400
            group = db.session.get(Group, group_id)
            if not group:
                return jsonify({'error': 'Group not found'}), 404
            membership = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
            # organizer is already a member
            if not membership and group.organizer_id != user_id:
                return jsonify({'error': 'Must be group member'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

#
def require_group_organizer(param_name='group_id'):
    """Ensure current user is the organizer/owner for the group. Supports routes that only have event_id."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # normalize identity to int
            raw_identity = get_jwt_identity()
            try:
                user_id = int(raw_identity)
            except (TypeError, ValueError):
                return jsonify({'error': 'Invalid token identity'}), 401

            group_id = kwargs.get(param_name)
            data = None
            if group_id is None:
                data = request.get_json(silent=True) or {}
                group_id = data.get(param_name)
            if group_id is None:
                # attempt derive from event_id
                if data is None:
                    data = request.get_json(silent=True) or {}
                event_id = kwargs.get('event_id') or data.get('event_id')
                if event_id is not None:
                    evt = db.session.get(Event, event_id)
                    if evt:
                        group_id = evt.group_id
            if group_id is None:
                return jsonify({'error': 'group_id not provided'}), 400
            # ensure int comparison
            try:
                group_id_int = int(group_id)
            except (TypeError, ValueError):
                return jsonify({'error': 'Invalid group_id'}), 400
            group = db.session.get(Group, group_id_int)
            if not group:
                return jsonify({'error': 'Group not found'}), 404
            if int(group.organizer_id) != user_id:
                return jsonify({'error': 'Only organizer permitted'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
