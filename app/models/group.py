from app.extensions import db

class Group(db.Model):
    __tablename__ = "Groups"
    group_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.user_id"))
    group_name = db.Column(db.String(45))
    members = db.relationship("GroupMember", backref="group")
    availabilities = db.relationship("Availability", backref="group")
