from app.extensions import db

class Calendar(db.Model):
    __tablename__ = "Calendar"
    calendar_id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum('personal', 'group'), nullable=False)
    owner_user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'), nullable=True)
    group_id = db.Column(db.Integer, db.ForeignKey('Groups.group_id'), nullable=True)
    name = db.Column(db.String(100))
    month = db.Column(db.Integer)
    year = db.Column(db.Integer)

    # Relationships
    owner_user = db.relationship('User', backref='personal_calendars', foreign_keys=[owner_user_id])
    group = db.relationship('Group', backref='group_for_calendar', foreign_keys=[group_id], overlaps="calendars,group_for_calendar")
    availabilities = db.relationship('Availability', backref='calendar', cascade='all, delete-orphan')
