

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db

calendar_bp = Blueprint('calendar', __name__)
from app.models import User, Group, Calendar, Availability, GroupMember



# Add event/notification to personal calendar (stored in Availability)
@calendar_bp.route('/personal/<int:calendar_id>/add_event', methods=['POST'])
@jwt_required()
def add_event_to_personal_calendar(calendar_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    date = data.get('date')
    status = data.get('status', 'event')
    description = data.get('description', '')
    if not date:
        return jsonify({'error': 'date required'}), 400
    # Create new Availability row for event
    from datetime import datetime
    try:
        event_date = datetime.strptime(date, "%Y-%m-%d").date()
    except Exception:
        return jsonify({'error': 'Invalid date format, expected YYYY-MM-DD'}), 400
    availability = Availability(user_id=user_id, calendar_id=calendar_id, date=event_date, status=status)
    db.session.add(availability)
    db.session.commit()
    return jsonify({'message': 'Event added to personal calendar', 'availability_id': availability.availability_id}), 201

# Fetch personal calendar for a user by month/year
@calendar_bp.route('/personal/<int:user_id>/<int:year>/<int:month>', methods=['GET'])
@jwt_required()
def get_personal_calendar(user_id, year, month):
    calendar = Calendar.query.filter_by(owner_user_id=user_id, type='personal').first()
    if not calendar:
        return jsonify({'error': 'Personal calendar not found'}), 404
    # Get all availabilities for this calendar
    availabilities = Availability.query.filter_by(calendar_id=calendar.calendar_id).all()
    avail_result = []
    for a in availabilities:
        item = {
            'availability_id': a.availability_id,
            'date': a.date.isoformat(),
            'status': a.status,
            'description': a.description
        }
        # If this is an event, include event details
        if a.status == 'event':
            item['name'] = a.name
            item['address'] = a.address
            item['place_id'] = a.place_id
            item['location_name'] = a.location_name
            item['description'] = a.description
        avail_result.append(item)
    # Get all events for this calendar and month/year
    from app.models import Event
    from sqlalchemy import extract
    events = Event.query.filter(
        Event.calendar_id == calendar.calendar_id,
        extract('year', Event.date) == year,
        extract('month', Event.date) == month
    ).all()
    event_result = []
    for e in events:
        event_result.append({
            'event_id': e.event_id,
            'date': e.date.isoformat(),
            'name': e.name,
            'description': e.description,
            'address': e.address,
            'location_name': e.location_name,
            'image_url': e.image_url,
            'google_maps_url': e.google_maps_url,
            'place_url': e.place_url,
            'start_time': e.start_time.strftime('%Y-%m-%d %H:%M') if e.start_time else None,
            'end_time': e.end_time.strftime('%Y-%m-%d %H:%M') if e.end_time else None,
            'finalized': e.finalized
        })
    return jsonify({
        'calendar_id': calendar.calendar_id,
        'month': month,
        'year': year,
        'availabilities': avail_result,
        'events': event_result
    }), 200


# Create personal calendar (from main menu, after login)
@calendar_bp.route('/create_personal', methods=['POST'])
@jwt_required()
def create_personal_calendar():
    user_id = get_jwt_identity()
    month = request.json.get('month')
    year = request.json.get('year') 
    name= request.json.get('name', 'Personal Calendar')
    existing = Calendar.query.filter_by(owner_user_id=user_id, type='personal').first()
    #If user already has personal calendar, do not create another
    if existing:
        return jsonify({'message': 'Personal calendar already exists.'}), 400
    
    calendar = Calendar(type='personal', owner_user_id=user_id, name=name, month=month, year=year)
    db.session.add(calendar)
    db.session.commit()
    return jsonify({'message': 'Personal calendar created.', 'calendar_id': calendar.calendar_id}), 201


# Endpoint to return calendar/group info
#Used to get user calendar info
from flask_jwt_extended import jwt_required, get_jwt_identity
@calendar_bp.route('/user_info', methods=['GET'])
@jwt_required()
def get_user_calendar_info():
    user_id = get_jwt_identity()
    requested_type = request.args.get('type', 'personal')
    if requested_type == 'group':
        group_id = request.args.get('group_id', type=int)
        if group_id:
            # Check if user is a member of this group
            group_member = GroupMember.query.filter_by(user_id=user_id, group_id=group_id).first()
            if not group_member:
                return jsonify({'error': 'User is not a member of this group'}), 403
            group_calendar = Calendar.query.filter_by(group_id=group_id, type='group').first()
            calendar_id = group_calendar.calendar_id if group_calendar else None
            calendar_type = 'group' if group_calendar else None
        else:
            # Fallback: first group membership
            group_member = GroupMember.query.filter_by(user_id=user_id).first()
            group_id = group_member.group_id if group_member else None
            group_calendar = Calendar.query.filter_by(group_id=group_id, type='group').first() if group_id else None
            calendar_id = group_calendar.calendar_id if group_calendar else None
            calendar_type = 'group' if group_calendar else None
    else:
        personal_calendar = Calendar.query.filter_by(owner_user_id=user_id, type='personal').first()
        calendar_id = personal_calendar.calendar_id if personal_calendar else None
        calendar_type = 'personal' if personal_calendar else None
        group_id = None
    return jsonify({
        'user_id': user_id,
        'calendar_id': calendar_id,
        'calendar_type': calendar_type,
        'group_id': group_id if requested_type == 'group' else None
    }), 200

# Get all availabilities for a calendar (Used in showing statuses on calendar view)
@calendar_bp.route('/<int:calendar_id>/availabilities', methods=['GET'])
@jwt_required()
def get_availabilities(calendar_id):
    availabilities = Availability.query.filter_by(calendar_id=calendar_id).all()
    result = [
        {
            'user_id': a.user_id,
            'date': a.date.isoformat(),
            'status': a.status,
            'description': a.description,
            'user_name': a.user.first_name 
        } for a in availabilities
    ]
    return jsonify(result), 200


#This is the main controller to set or update availability
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
    #Optional: get description also
    description = data.get('description')
    if not date or not status:
        return jsonify({'error': 'date and status required'}), 400
    availability = Availability.query.filter_by(user_id=user_id, calendar_id=calendar_id, date=date).first()
    if availability:
        availability.status = status
        #only set description if provided
        if description is not None:
            availability.description = description
    else:
        availability = Availability(user_id=user_id, calendar_id=calendar_id, date=date, status=status, description=description)
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
    #Only update description if provided
    description = data.get('description')
    availability = db.session.get(Availability, availability_id)
    if not availability or availability.user_id != user_id or availability.calendar_id != calendar_id:
        return jsonify({'error': 'Availability not found or unauthorized'}), 404
    if status:
        availability.status = status
    if date:
        availability.date = date
    #Only update description if provided
    if description is not None:
        availability.description = description
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
    if group.organizer_id not in member_ids:
        member_ids.append(group.organizer_id)
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

#For Future Use
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
    if group.organizer_id not in member_ids:
        member_ids.append(group.organizer_id)
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


# Update availability for a specific date
@calendar_bp.route('/<int:calendar_id>/availability/<int:availability_id>', methods=['PUT'])
@jwt_required()
def update_availability(calendar_id, availability_id):
    data = request.get_json()
    raw_identity = get_jwt_identity()
    try:
        user_id = int(raw_identity)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid token identity'}), 401
    availability = Availability.query.filter_by(availability_id=availability_id, calendar_id=calendar_id, user_id=user_id).first()
    if not availability:
        return jsonify({'error': 'Availability not found or not permitted'}), 404
    status = data.get('status')
    if status:
        availability.status = status
    db.session.commit()
    return jsonify({'message': 'Availability updated'}), 200

# Delete availability for a specific date
@calendar_bp.route('/<int:calendar_id>/availability/<int:availability_id>', methods=['DELETE'])
@jwt_required()
def delete_availability(calendar_id, availability_id):
    raw_identity = get_jwt_identity()
    try:
        user_id = int(raw_identity)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid token identity'}), 401
    availability = Availability.query.filter_by(availability_id=availability_id, calendar_id=calendar_id, user_id=user_id).first()
    if not availability:
        return jsonify({'error': 'Availability not found or not permitted'}), 404
    db.session.delete(availability)
    db.session.commit()
    return jsonify({'message': 'Availability deleted'}), 200


# Get all availabilities for a user in a calendar
@calendar_bp.route('/<int:calendar_id>/user/<int:user_id>/availabilities', methods=['GET'])
@jwt_required()
def get_user_availabilities(calendar_id, user_id):
    availabilities = Availability.query.filter_by(calendar_id=calendar_id, user_id=user_id).all()
    result = [{'date': a.date.isoformat(), 'status': a.status} for a in availabilities]
    return jsonify(result), 200

# Get merged availabilities for group shared calendar
@calendar_bp.route('/api/group/<int:group_id>/shared_calendar', methods=['GET'])
def get_group_shared_calendar(group_id):
    group = Group.query.get(group_id)
    if not group:
        return jsonify({'message': 'Group not found.'}), 404
    calendar = Calendar.query.filter_by(group_id=group_id, type='group').first()
    if not calendar:
        return jsonify({'message': 'Group calendar not found.'}), 404
    # Only include availabilities of accepted group members
    member_ids = [gm.user_id for gm in group.members]
    if group.organizer_id not in member_ids:
        member_ids.append(group.organizer_id)
    availabilities = Availability.query.filter(Availability.calendar_id == calendar.calendar_id, Availability.user_id.in_(member_ids)).all()
    result = [
        {
            'availability_id': a.availability_id,
            'user_id': a.user_id,
            'date': a.date.strftime('%Y-%m-%d'),
            'status': a.status
        } for a in availabilities
    ]
    return jsonify({'availabilities': result}), 200


#For Future use
# List all group calendars for a user (including old/ended sessions)
@calendar_bp.route('/user/<int:user_id>/group_calendars', methods=['GET'])
@jwt_required()
def list_group_calendars_for_user(user_id):
    # Find all groups where user is a member or organizer
    group_ids = [gm.group_id for gm in GroupMember.query.filter_by(user_id=user_id).all()]
    organized_group_ids = [g.group_id for g in Group.query.filter_by(organizer_id=user_id).all()]
    all_group_ids = set(group_ids + organized_group_ids)
    calendars = Calendar.query.filter(Calendar.group_id.in_(all_group_ids), Calendar.type=='group').all()
    result = [
        {
            'calendar_id': c.calendar_id,
            'group_id': c.group_id,
            'name': c.name,
            'month': c.month,
            'year': c.year
        } for c in calendars
    ]
    return jsonify({'group_calendars': result}), 200