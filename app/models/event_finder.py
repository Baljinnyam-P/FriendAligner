from app.extensions import db

class EventFinder(db.Model):
    __tablename__ = "Event Finder"
    eventFinder_id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("Groups.group_id"))
    calendar_id = db.Column(db.Integer, db.ForeignKey("Calendar.calendar_id"))
    zip_code = db.Column(db.String(45))
    # Relationships
    calendar = db.relationship("Calendar", backref="event_finders")
    group = db.relationship("Group", backref="event_finders")
