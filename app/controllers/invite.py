from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import User, Group, Invite, Notification
from datetime import datetime
from flask import current_app
import smtplib
from email.mime.text import MIMEText
from app.models import GroupMember
import os

invite_bp = Blueprint('invite', __name__)

#Not Complete
@invite_bp.route('/send', methods=['POST'])
@jwt_required()
def send_invite():
    data = request.get_json()
    group_id = data.get('group_id')
    invited_user_id = data.get('invited_user_id')
    calendar_id = data.get('calendar_id')
    # get sender id from jwt
    raw_identity = get_jwt_identity()
    try:
        sender_id = int(raw_identity)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid token identity'}), 401

    # If no group_id, create group for calendar/user
    group = None
    new_group_created = False
    if not group_id:
        group_name = f"Calendar Group {calendar_id or sender_id}"
        group = Group(group_name=group_name, user_id=sender_id)
        db.session.add(group)
        db.session.commit()
        group_id = group.group_id
        new_group_created = True
    else:
        group = db.session.get(Group, group_id)
        if not group:
            return jsonify({'error': 'Group not found'}), 404

    # Check if invited user exists
    invited_user = db.session.get(User, invited_user_id)
    if not invited_user:
        return jsonify({'error': 'User not found'}), 404

    # Accept date from frontend
    date_str = data.get('date')
    invite_date = None
    if date_str:
        try:
            invite_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            return jsonify({'error': 'Invalid date format, expected YYYY-MM-DD'}), 400
    # Create invite
    invite = Invite(group_id=group_id, invited_user_id=invited_user_id, sender_id=sender_id, status='pending', date=invite_date)
    db.session.add(invite)
    db.session.commit()

    # Create notification (in-app)
    notif_msg = f"You have been invited to join group '{group.group_name}' by {db.session.get(User, sender_id).first_name}"
    notification = Notification(user_id=invited_user_id, message=notif_msg, type='invite')
    db.session.add(notification)
    db.session.commit()

    # Send email notification (if email exists)
    recipient_email = invited_user.email
    if recipient_email:
        subject = "Group Invite Notification"
        body = notif_msg
        send_email(recipient_email, subject, body)

    response = {'message': 'Invite sent successfully'}
    if new_group_created:
        response['group_id'] = group_id
    return jsonify(response), 201

def send_email(to_email, subject, body):
    smtp_server = current_app.config.get('SMTP_SERVER')
    smtp_port = current_app.config.get('SMTP_PORT')
    smtp_user = current_app.config.get('SMTP_USER')
    smtp_password = current_app.config.get('SMTP_PASSWORD')
    from_email = smtp_user
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(from_email, [to_email], msg.as_string())
    except Exception as e:
        print(f"Email send failed: {e}")

@invite_bp.route('/respond', methods=['POST'])
@jwt_required()
def respond_invite():
    data = request.get_json()
    invite_id = data.get('invite_id')
    response = data.get('response')  # 'accepted' or 'declined'
    raw_identity = get_jwt_identity()
    try:
        user_id = int(raw_identity)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid token identity'}), 401

    invite = db.session.get(Invite, invite_id)
    if not invite or invite.invited_user_id != user_id:
        return jsonify({'error': 'Invite not found or unauthorized'}), 404

    if response not in ['accepted', 'declined']:
        return jsonify({'error': 'Invalid response'}), 400

    invite.status = response
    db.session.commit()

    # Create notification for sender (in-app)
    sender_id = invite.sender_id
    group = db.session.get(Group, invite.group_id)
    invited_user = db.session.get(User, user_id)
    # If group does not exist (edge case), create it
    if not group:
        group_name = f"Calendar Group {invite.group_id or sender_id}"
        group = Group(group_name=group_name, user_id=sender_id)
        db.session.add(group)
        db.session.commit()
        invite.group_id = group.group_id
        db.session.commit()
    notif_msg = f"{invited_user.first_name} has {response} your invite to group '{group.group_name}'"
    notification = Notification(user_id=sender_id, message=notif_msg, type='invite_response')
    db.session.add(notification)
    db.session.commit()

    # Send email notification to sender
    sender = db.session.get(User, sender_id)
    if sender and sender.email:
        subject = "Invite Response Notification"
        body = notif_msg
        send_email(sender.email, subject, body)

    # If accepted, add user to group
    if response == 'accepted' and group:
        
        if not GroupMember.query.filter_by(group_id=group.group_id, user_id=invited_user.user_id).first():
            gm = GroupMember(group_id=group.group_id, user_id=invited_user.user_id, role='member')
            db.session.add(gm)
        db.session.commit()
    return jsonify({'message': f'Invite {response}'}), 200

@invite_bp.route('/invite/pending', methods=['GET'])
@jwt_required()
def get_pending_invites():
    user_id = get_jwt_identity()
    invites = Invite.query.filter_by(invited_user_id=user_id, status='pending').all()
    result = [
        {
            'invite_id': invite.invite_id,
            'group_id': invite.group_id,
            'sender_id': invite.sender_id,
            'status': invite.status,
            'date': invite.date.isoformat() if invite.date else None,
            'invited_user_id': invite.invited_user_id
        } for invite in invites
    ]
    return jsonify(result), 200

# Generate invite link (organizer only)
@invite_bp.route('/invite/link', methods=['POST'])
@jwt_required()
def generate_invite_link():
    data = request.get_json()
    group_id = data.get('group_id')
    email = data.get('email')
    if not email:
        return jsonify({'error': 'email required'}), 400
    token = os.urandom(16).hex()
    raw_identity = get_jwt_identity()
    try:
        sender_id = int(raw_identity)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid token identity'}), 401
    invite = Invite(group_id=group_id, email=email, token=token, status='pending', sender_id=sender_id)
    db.session.add(invite)
    db.session.commit()
    link = f"{request.host_url.rstrip('/')}/api/invite/{token}"  # shareable link
    return jsonify({'invite_link': link, 'token': token}), 201

# Fetch invite info by token (public)
@invite_bp.route('/invite/<token>', methods=['GET'])
def get_invite_by_token(token):
    invite = Invite.query.filter_by(token=token).first()
    if not invite:
        return jsonify({'error': 'Invite not found'}), 404
    group = db.session.get(Group, invite.group_id)
    return jsonify({
        'invite_id': invite.invite_id,
        'group_name': group.group_name if group else None,
        'status': invite.status
    }), 200

# Respond to invite via token (accept/decline) requires email match
@invite_bp.route('/invite/<token>/respond', methods=['POST'])
def respond_invite_token(token):
    data = request.get_json()
    response = data.get('response')  # accepted / declined
    email = data.get('email')
    if response not in ['accepted', 'declined']:
        return jsonify({'error': 'Invalid response'}), 400
    invite = Invite.query.filter_by(token=token).first()
    if not invite or invite.status != 'pending':
        return jsonify({'error': 'Invite not found or not pending'}), 404
    if invite.email != email:
        return jsonify({'error': 'Email mismatch'}), 403
    invite.status = response
    db.session.commit()
    group = db.session.get(Group, invite.group_id)
    organizer_id = group.user_id if group else None
    user = User.query.filter_by(email=email).first()
    # If accepted and user exists, add membership
    if response == 'accepted':
        if user:
            invite.invited_user_id = user.user_id
            if group:
                if not GroupMember.query.filter_by(group_id=group.group_id, user_id=user.user_id).first():
                    gm = GroupMember(group_id=group.group_id, user_id=user.user_id, role='member')
                    db.session.add(gm)
        else:
            # User must register first
            db.session.commit()
            return jsonify({'message': 'Invite accepted pending registration. Please create an account with this email.'}), 200
    # Notify organizer if exists
    if organizer_id:
        notif_msg = f"Invite email {email} has {response} the group invite."
        n = Notification(user_id=organizer_id, message=notif_msg, type='invite_response')
        db.session.add(n)
    db.session.commit()
    return jsonify({'message': f'Invite {response}'}), 200
