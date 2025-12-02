from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import Group, GroupMember, User, Calendar, Availability
from app.models.notification import Notification
from app.utils.send_email import send_email


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
    month = data.get('month')
    year = data.get('year')
    if not group_name or not month or not year:
        return jsonify({'error': 'group_name, month, year required'}), 400
    # Create group and add organizer as member
    group = Group(group_name=group_name, organizer_id=user_id, month=month, year=year)
    db.session.add(group)
    db.session.commit()
    calendar = Calendar(group_id=group.group_id, month=month, year=year, name=f"{group_name} Calendar", type='group')
    db.session.add(calendar)
    db.session.commit()
    gm = GroupMember(group_id=group.group_id, user_id=user_id, role='organizer')
    db.session.add(gm)
    db.session.commit()
    return jsonify({'message': 'Group and calendar created', 'group_id': group.group_id, 'calendar_id': calendar.calendar_id}), 201

# Add member to group (organizer only)
@group_bp.route('/group/<int:group_id>/add_member', methods=['POST'])
@jwt_required()
def add_member(group_id):
    # Only organizer can add members
    data = request.get_json()
    new_user_id = data.get('user_id')
    raw_identity = get_jwt_identity()
    group = db.session.get(Group, group_id)
    if not new_user_id:
        return jsonify({'error': 'user_id required'}), 400
    if not group or int(raw_identity) != group.organizer_id:
        return jsonify({'error': 'Only organizer can add members'}), 403
    if GroupMember.query.filter_by(group_id=group_id, user_id=new_user_id).first():
        return jsonify({'error': 'User already in group'}), 400
    member = GroupMember(group_id=group_id, user_id=new_user_id, role='member')
    db.session.add(member)
    db.session.commit()
    # Merge personal availabilities into group calendar
    personal_calendar = Calendar.query.filter_by(owner_user_id=new_user_id, type='personal').first()
    group_calendar = Calendar.query.filter_by(group_id=group_id, type='group').first()
    if personal_calendar and group_calendar:
        personal_avails = Availability.query.filter_by(calendar_id=personal_calendar.calendar_id).all()
        for avail in personal_avails:
            exists = Availability.query.filter_by(calendar_id=group_calendar.calendar_id, user_id=avail.user_id, date=avail.date).first()
            if not exists:
                new_avail = Availability(user_id=avail.user_id, calendar_id=group_calendar.calendar_id, date=avail.date, status=avail.status)
                db.session.add(new_avail)
        db.session.commit()
    return jsonify({'message': 'Member added', 'group_member_id': member.gm_id}), 201

# Remove member from group (organizer only)
@group_bp.route('/<int:group_id>/remove_member', methods=['POST'])
@jwt_required()
def remove_member(group_id):
    # Only organizer can remove members
    data = request.get_json()
    remove_user_id = data.get('user_id')
    raw_identity = get_jwt_identity()
    group = db.session.get(Group, group_id)
    if not remove_user_id:
        return jsonify({'error': 'user_id required'}), 400
    if not group or int(raw_identity) != group.organizer_id:
        return jsonify({'error': 'Only organizer can remove members'}), 403
    member = GroupMember.query.filter_by(group_id=group_id, user_id=remove_user_id).first()
    if not member:
        return jsonify({'error': 'User not in group'}), 404
    db.session.delete(member)
    # Remove member's availabilities from the shared group calendar
    group_calendar = Calendar.query.filter_by(group_id=group_id, type='group').first()
    if group_calendar:
        Availability.query.filter_by(calendar_id=group_calendar.calendar_id, user_id=remove_user_id).delete()
    db.session.commit()
    # Notify remaining members about the removal
    remaining_members = GroupMember.query.filter_by(group_id=group_id).all()
    removed_user = db.session.get(User, remove_user_id)
    removed_name = f"{removed_user.first_name} {removed_user.last_name}" if removed_user else "A member"
    notif_msg = f"{removed_name} has left the group '{group.group_name}'."
    for m in remaining_members:
        notification = Notification(user_id=m.user_id, message=notif_msg, type='group_member_removed')
        db.session.add(notification)
        member_user = db.session.get(User, m.user_id)
        if member_user and member_user.email:
            send_email(member_user.email, "Group Member Removed", notif_msg)
    db.session.commit()
    return jsonify({'message': 'Member removed'}), 200

# End group session (organizer only)
@group_bp.route('/<int:group_id>/end_session', methods=['POST'])
@jwt_required()
def end_group_session(group_id):
    raw_identity = get_jwt_identity()
    group = db.session.get(Group, group_id)
    if not group:
        return jsonify({'error': 'Group not found'}), 404
    if int(raw_identity) != group.organizer_id:
        return jsonify({'error': 'Only organizer can end session'}), 403
    # Get all members
    members = GroupMember.query.filter_by(group_id=group_id).all()
    member_ids = [m.user_id for m in members]
    # Get group calendar
    group_calendar = Calendar.query.filter_by(group_id=group_id, type='group').first()
    # Remove all availabilities for group calendar
    if group_calendar:
        Availability.query.filter_by(calendar_id=group_calendar.calendar_id).delete()
        db.session.delete(group_calendar)
    # Remove all group members
    for m in members:
        db.session.delete(m)
    # Notify all members
    notif_msg = f"The group session '{group.group_name}' has ended. You have been removed from the group and shared calendar."
    for user_id in member_ids:
        notification = Notification(user_id=user_id, message=notif_msg, type='group_session_ended')
        db.session.add(notification)
        member_user = db.session.get(User, user_id)
        if member_user and member_user.email:
            send_email(member_user.email, "Group Session Ended", notif_msg)
    # Delete group
    db.session.delete(group)
    db.session.commit()
    return jsonify({'message': 'Group session ended, members removed, calendar deleted, notifications sent.'}), 200

# View all members in a group
@group_bp.route('/<int:group_id>/members', methods=['GET'])
@jwt_required()
def get_group_members(group_id):
    group = db.session.get(Group, group_id)
    if not group:
        return jsonify({'error': 'Group not found'}), 404
    members = GroupMember.query.filter_by(group_id=group_id).all()
    member_list = []
    for m in members:
        user = db.session.get(User, m.user_id)
        if user:
            member_list.append({
                'user_id': user.user_id,
                'first_name': user.first_name,
                'last_name': user.last_name
            })
    return jsonify({
        'group_name': group.group_name,
        'organizer_id': group.organizer_id,
        'members': member_list
    }), 200


#For future use
# Get group's calendar's name, year and month if needed
@group_bp.route('/group/<int:group_id>/calendar', methods=['GET'])
@jwt_required()
def get_group_calendar(group_id):
    calendar = Calendar.query.filter_by(group_id=group_id, type='group').first()
    if not calendar:
        return jsonify({'error': 'Calendar not found'}), 404
    return jsonify({
        'calendar_id': calendar.calendar_id,
        'month': calendar.month,
        'year': calendar.year,
        'name': calendar.name
    }), 200

# Get all groups for current user
@group_bp.route('/user/groups', methods=['GET'])
@jwt_required()
def user_groups():
    user_id = get_jwt_identity()
    groups = (
        db.session.query(Group)
        .join(GroupMember, Group.group_id == GroupMember.group_id)
        .filter(GroupMember.user_id == user_id)
        .all()
    )
    group_list = []
    for group in groups:
        organizer = db.session.get(User, group.organizer_id)
        members = (
            db.session.query(User)
            .join(GroupMember, User.user_id == GroupMember.user_id)
            .filter(GroupMember.group_id == group.group_id)
            .all()
        )
        group_list.append({
            'group_id': group.group_id,
            'group_name': group.group_name,
            'organizer': {
                'first_name': organizer.first_name if organizer else '',
                'last_name': organizer.last_name if organizer else ''
            },
            'members': [
                {'first_name': m.first_name, 'last_name': m.last_name} for m in members
            ]
        })
    return jsonify({'groups': group_list})


# Get all groups that current user organizes
@group_bp.route('/user/organized_groups', methods=['GET'])
@jwt_required()
def user_organized_groups():
    user_id = get_jwt_identity()
    groups = Group.query.filter_by(organizer_id=user_id).all()
    group_list = []
    for group in groups:
        members = (
            db.session.query(User)
            .join(GroupMember, User.user_id == GroupMember.user_id)
            .filter(GroupMember.group_id == group.group_id)
            .all()
        )
        group_list.append({
            'group_id': group.group_id,
            'group_name': group.group_name,
            'members': [
                {'first_name': m.first_name, 'last_name': m.last_name} for m in members
            ]
        })
    return jsonify({'organized_groups': group_list})
