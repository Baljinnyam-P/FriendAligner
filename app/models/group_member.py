from app.extensions import db

class GroupMember(db.Model):
    __tablename__ = "Group Members"
    gm_id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("Groups.group_id"))
    user_id = db.Column(db.Integer, db.ForeignKey("Users.user_id"))
    role = db.Column(db.String(45))
