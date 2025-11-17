from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import User, Group, Calendar, Availability, GroupMember

calendar_bp = Blueprint('calendar', __name__)

@calendar_bp.route('/create', methods=['POST'])
@jwt_required()
def create_calendar():
    data = request.get_json()
    raw_identity = get_jwt_identity()
    try:
        user_id = int(raw_identity)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid token identity'}), 401
    name = data.get('name')
    calendar = Calendar(user_id=user_id, name=name)
    db.session.add(calendar)
    db.session.commit()
    return jsonify({'message': 'Calendar created', 'calendar_id': calendar.calendar_id}), 201

@calendar_bp.route('/<int:calendar_id>', methods=['GET'])
@jwt_required()
def get_calendar(calendar_id):
    calendar = db.session.get(Calendar, calendar_id)
    if not calendar:
        return jsonify({'error': 'Calendar not found'}), 404
    return jsonify({'calendar_id': calendar.calendar_id, 'name': calendar.name, 'user_id': calendar.user_id}), 200

@calendar_bp.route('/<int:calendar_id>/update', methods=['PUT'])
@jwt_required()
def update_calendar(calendar_id):
    data = request.get_json()
    calendar = db.session.get(Calendar, calendar_id)
    if not calendar:
        return jsonify({'error': 'Calendar not found'}), 404
    calendar.name = data.get('name', calendar.name)
    db.session.commit()
    return jsonify({'message': 'Calendar updated'}), 200


#Set or update user's availability for a specific date.
#If an entry exists, update it. Otherwise, create new.
@calendar_bp.route('/<int:calendar_id>/availability', methods=['POST'])
@jwt_required()
def set_or_update_availability(calendar_id):
    data = request.get_json()
    raw_identity = get_jwt_identity()
    try:
        user_id = int(raw_identity)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid token identity'}), 401
    date = data.get('date')
    status = data.get('status', 'pending')
    group_id = data.get('group_id')
    if not date or not status:
        return jsonify({'error': 'date and status required'}), 400
    availability = Availability.query.filter_by(user_id=user_id, calendar_id=calendar_id, date=date).first()
    if availability:
        availability.status = status
        if group_id:
            availability.group_id = group_id
    else:
        availability = Availability(user_id=user_id, calendar_id=calendar_id, date=date, status=status, group_id=group_id)
        db.session.add(availability)
    db.session.commit()
    return jsonify({'message': 'Availability set/updated', 'availability_id': availability.availability_id}), 200


# Edit an existing availability (status or date)
#Only the owner can edit their own availability.
@calendar_bp.route('/<int:calendar_id>/availability/<int:availability_id>', methods=['PUT'])
@jwt_required()
def edit_availability(calendar_id, availability_id):
    raw_identity = get_jwt_identity()
    try:
        user_id = int(raw_identity)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid token identity'}), 401
    data = request.get_json()
    status = data.get('status')
    date = data.get('date')
    availability = db.session.get(Availability, availability_id)
    if not availability or availability.user_id != user_id or availability.calendar_id != calendar_id:
        return jsonify({'error': 'Availability not found or unauthorized'}), 404
    if status:
        availability.status = status
    if date:
        availability.date = date
    db.session.commit()
    return jsonify({'message': 'Availability updated'}), 200

# View a user's availability for a specific date
@calendar_bp.route('/<int:calendar_id>/availability/<int:user_id>/<date>', methods=['GET'])
@jwt_required()
def get_user_availability(calendar_id, user_id, date):
    availability = Availability.query.filter_by(user_id=user_id, calendar_id=calendar_id, date=date).first()
    if not availability:
        return jsonify({'error': 'Availability not found'}), 404
    return jsonify({
        'availability_id': availability.availability_id,
        'user_id': availability.user_id,
        'calendar_id': availability.calendar_id,
        'date': str(availability.date),
        'status': availability.status
    }), 200

# Group availability aggregation for a date
@calendar_bp.route('/<int:calendar_id>/group_availability', methods=['GET'])
@jwt_required()
def group_availability(calendar_id):
    date = request.args.get('date')
    group_id = request.args.get('group_id')
    if not date or not group_id:
        return jsonify({'error': 'date and group_id required'}), 400
    group = db.session.get(Group, group_id)
    if not group:
        return jsonify({'error': 'Group not found'}), 404
    # Collect member ids (organizer + members)
    member_ids = [m.user_id for m in GroupMember.query.filter_by(group_id=group_id).all()]
    if group.user_id not in member_ids:
        member_ids.append(group.user_id)
    avail_rows = Availability.query.filter_by(group_id=group_id, calendar_id=calendar_id, date=date).all()
    by_user = {}
    # Get all user objects for member_ids
    user_objs = {u.user_id: u for u in User.query.filter(User.user_id.in_(member_ids)).all()}
    for row in avail_rows:
        slots = by_user.setdefault(row.user_id, [])
        slots.append({
            'availability_id': row.availability_id,
            'status': row.status
        })
    users_info = {}
    for uid in member_ids:
        user = user_objs.get(uid)
        name = f"{user.first_name} {user.last_name}" if user else f"User {uid}"
        users_info[uid] = {
            'name': name,
            'slots': by_user.get(uid, [{'status': 'pending'}])
        }
    return jsonify({'date': date, 'group_id': int(group_id), 'users': users_info}), 200

# Check if everyone available for a date
@calendar_bp.route('/<int:calendar_id>/everyone_available', methods=['GET'])
@jwt_required()
def everyone_available(calendar_id):
    date = request.args.get('date')
    group_id = request.args.get('group_id')
    if not date or not group_id:
        return jsonify({'error': 'date and group_id required'}), 400
    group = db.session.get(Group, group_id)
    if not group:
        return jsonify({'error': 'Group not found'}), 404
    member_ids = [m.user_id for m in GroupMember.query.filter_by(group_id=group_id).all()]
    if group.user_id not in member_ids:
        member_ids.append(group.user_id)
    # For each member ensure at least one availability with status 'available'
    all_available = True
    details = {}
    for uid in member_ids:
        rows = Availability.query.filter_by(group_id=group_id, calendar_id=calendar_id, date=date, user_id=uid).all()
        user_has = any(r.status == 'available' for r in rows)
        details[uid] = {'available': user_has, 'total_slots': len(rows)}
        if not user_has:
            all_available = False
    return jsonify({'date': date, 'group_id': int(group_id), 'everyone_available': all_available, 'details': details}), 200

#Not Complete
@calendar_bp.route('/<int:calendar_id>/fully_available_days', methods=['GET'])
@jwt_required()
def fully_available_days(calendar_id):
    group_id = request.args.get('group_id')
    if not group_id:
        return jsonify({'error': 'group_id required'}), 400
    group = db.session.get(Group, group_id)
    if not group:
        return jsonify({'error': 'Group not found'}), 404
    member_ids = [m.user_id for m in GroupMember.query.filter_by(group_id=group_id).all()]
    if group.user_id not in member_ids:
        member_ids.append(group.user_id)
    # Fetch all availability rows for group/calendar
    rows = Availability.query.filter_by(group_id=group_id, calendar_id=calendar_id).all()
    by_date = {}
    for r in rows:
        if not r.date:
            continue
        date_key = r.date.isoformat()
        user_set = by_date.setdefault(date_key, set())
        if r.status == 'available':
            user_set.add(r.user_id)
    fully = [d for d, users in by_date.items() if len(users) == len(member_ids)]
    return jsonify({'group_id': int(group_id), 'calendar_id': calendar_id, 'fully_available_dates': sorted(fully)}), 200
