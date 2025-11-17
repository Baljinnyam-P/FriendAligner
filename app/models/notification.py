from app.extensions import db
from datetime import datetime

class Notification(db.Model):
    __tablename__ = "Notifications"
    notification_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.user_id"), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(30))  # invite, reminder, event_finalized, response
    event_id = db.Column(db.Integer, db.ForeignKey("Events.event_id"))  # optional link to event
    scheduled_at = db.Column(db.DateTime, nullable=True)  # for reminders/day-before
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)
    sent = db.Column(db.Boolean, default=False)  # whether scheduled notification has been sent
