from app.extensions import db

class GroupMember(db.Model):
    __tablename__ = "Group Members"
    gm_id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("Groups.group_id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.user_id"), nullable=False)
    role = db.Column(db.String(45))

    user = db.relationship('User', backref='group_member_links', overlaps="group_member_links,user_link")
    group = db.relationship('Group', backref='group_members', overlaps="group_link,members")
