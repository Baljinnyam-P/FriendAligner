from app.extensions import db

class Group(db.Model):
    __tablename__ = "Groups"
    group_id = db.Column(db.Integer, primary_key=True)
    organizer_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'), nullable=False)
    group_name = db.Column(db.String(45), nullable=False)

    organizer = db.relationship('User', backref='organized_groups', overlaps="groups,owner")
    members = db.relationship('GroupMember', backref='group_link', cascade='all, delete-orphan', overlaps="group_link,members")
    calendars = db.relationship('Calendar', backref='group_for_calendar', uselist=False, foreign_keys='Calendar.group_id', overlaps="group_for_calendar")
