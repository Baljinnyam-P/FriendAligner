from datetime import datetime, date, time
from app.extensions import db

class Event(db.Model):
    __tablename__ = "Events"
    event_id = db.Column(db.Integer, primary_key=True)
    calendar_id = db.Column(db.Integer, db.ForeignKey("Calendar.calendar_id"), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey("Groups.group_id"), nullable=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("Users.user_id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    address = db.Column(db.String(255), nullable=True)
    location_name = db.Column(db.String(120), nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    google_maps_url = db.Column(db.String(255), nullable=True)
    place_url = db.Column(db.String(255), nullable=True)
    finalized = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = db.relationship("User", backref="created_events", foreign_keys=[created_by_user_id])
    group = db.relationship("Group", backref="events")
    calendar = db.relationship("Calendar", backref="events")
    notifications = db.relationship("Notification", backref="event", lazy='dynamic')
