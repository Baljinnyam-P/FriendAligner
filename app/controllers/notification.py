from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import Notification, User, Event, Group, Availability, GroupMember
from datetime import datetime, timedelta
from flask import current_app
import smtplib
from email.mime.text import MIMEText

notification_bp = Blueprint('notification', __name__)

#Get all notifications for current user
@notification_bp.route('/', methods=['GET'])
@jwt_required()
def get_notifications():
    raw_identity = get_jwt_identity()
    try:
        user_id = int(raw_identity)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid token identity'}), 401
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
    result = []
    from app.models import Invite
    for n in notifications:
        notif = {
            'notification_id': n.notification_id,
            'message': n.message,
            'type': n.type,
            'created_at': n.created_at.isoformat() if n.created_at else None,
            'scheduled_at': n.scheduled_at.isoformat() if n.scheduled_at else None,
            'event_id': n.event_id,
            'read': n.read,
            'sent': n.sent
        }
        # If invite notification, attach invite_id and status
        if n.type == 'invite':
            invite = Invite.query.filter_by(invited_user_id=n.user_id, status='pending').order_by(Invite.invite_id.desc()).first()
            if invite:
                notif['invite_id'] = invite.invite_id
                notif['status'] = invite.status
        result.append(notif)
    return jsonify(result), 200


# Mark notification as read (active)
@notification_bp.route('/<int:notification_id>/read', methods=['POST'])
@jwt_required()
def mark_read(notification_id):
    raw_identity = get_jwt_identity()
    try:
        user_id = int(raw_identity)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid token identity'}), 401
    notification = db.session.get(Notification, notification_id)
    if not notification or notification.user_id != user_id:
        return jsonify({'error': 'Notification not found or unauthorized'}), 404
    notification.read = True
    db.session.commit()
    return jsonify({'message': 'Notification marked as read'}), 200

# Create a notification (for backend use)
@notification_bp.route('/notifications', methods=['POST'])
@jwt_required()
def create_notification():
    data = request.get_json()
    user_id = data.get('user_id')
    message = data.get('message')
    type_ = data.get('type', 'event')
    if not user_id or not message:
        return jsonify({'error': 'user_id and message required'}), 400
    notification = Notification(user_id=user_id, message=message, type=type_)
    db.session.add(notification)
    db.session.commit()
    return jsonify({'message': 'Notification created', 'notification_id': notification.notification_id}), 201

#For future use
# Schedule day-before event reminder for all group members
@notification_bp.route('/notifications/event/<int:event_id>/schedule_reminder', methods=['POST'])
@jwt_required()
def schedule_event_reminder(event_id):
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    # day-before at 09:00 server time
    if not event.date:
        return jsonify({'error': 'Event date missing'}), 400
    reminder_dt = datetime.combine(event.date, datetime.min.time()) - timedelta(days=1) + timedelta(hours=9)
    group = db.session.get(Group, event.group_id)
    member_ids = [group.organizer_id] if group else []
    if group:
        member_ids += [m.user_id for m in group.members]
    created = []
    for uid in set(member_ids):
        msg = f"Reminder: Event '{event.name}' tomorrow ({event.date})."
        n = Notification(user_id=uid, message=msg, type='reminder', event_id=event.event_id, scheduled_at=reminder_dt)
        db.session.add(n)
        created.append(uid)
    db.session.commit()
    return jsonify({'message': 'Reminders scheduled', 'user_ids': created, 'scheduled_at': reminder_dt.isoformat()}), 201

#For future use
# Send due scheduled notifications (in-app + email) that are unsent
@notification_bp.route('/notifications/send_due', methods=['POST'])
@jwt_required()
def send_due_notifications():
    now = datetime.utcnow()
    due = Notification.query.filter(Notification.scheduled_at.isnot(None), Notification.scheduled_at <= now, Notification.sent == False).all()
    count = 0
    for n in due:
        # email if user has email
        user = db.session.get(User, n.user_id)
        if user and user.email:
            _send_email(user.email, f"{n.type.capitalize()} Notification", n.message)
        n.sent = True
        count += 1
    db.session.commit()
    return jsonify({'message': 'Due notifications dispatched', 'count': count}), 200

#For future use
# Remind non-responders (no availability 'available') for event date
@notification_bp.route('/notifications/event/<int:event_id>/remind_nonresponders', methods=['POST'])
@jwt_required()
def remind_nonresponders(event_id):
    event = db.session.get(Event, event_id)
    if not event or not event.date:
        return jsonify({'error': 'Event not found or date missing'}), 404
    group = db.session.get(Group, event.group_id)
    member_ids = [group.organizer_id] if group else []
    if group:
        member_ids += [m.user_id for m in group.members]
    reminded = []
    for uid in set(member_ids):
        rows = Availability.query.filter_by(group_id=group.group_id, date=event.date, user_id=uid).all()
        has_available = any(r.status == 'available' for r in rows)
        if not has_available:
            msg = f"Please update availability for event '{event.name}' on {event.date}."
            n = Notification(user_id=uid, message=msg, type='reminder', event_id=event.event_id)
            db.session.add(n)
            user = db.session.get(User, uid)
            if user and user.email:
                _send_email(user.email, "Availability Reminder", msg)
            reminded.append(uid)
    db.session.commit()
    return jsonify({'message': 'Non-responders reminded', 'user_ids': reminded}), 200


#This used to send email notifications
def _send_email(to_email, subject, body):
    smtp_server = current_app.config.get('SMTP_SERVER')
    smtp_port = current_app.config.get('SMTP_PORT')
    smtp_user = current_app.config.get('SMTP_USER')
    smtp_password = current_app.config.get('SMTP_PASSWORD')
    if not smtp_server or not smtp_user or not smtp_password:
        return  
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = smtp_user
    msg['To'] = to_email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, [to_email], msg.as_string())
    except Exception as e:
        print(f"Email send failed: {e}")
