from datetime import datetime, date, time
from app.extensions import db

class Event(db.Model):
    __tablename__ = "Events"
    event_id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("Groups.group_id"), nullable=False)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("Users.user_id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    place_id = db.Column(db.String(64), nullable=True)
    location_name = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    finalized = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    creator = db.relationship("User", backref="created_events")
    group = db.relationship("Group", backref="events")
    notifications = db.relationship("Notification", backref="event", lazy='dynamic')
