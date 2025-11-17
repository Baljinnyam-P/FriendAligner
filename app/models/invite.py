from app.extensions import db

class Invite(db.Model):
    __tablename__ = "Invites"
    invite_id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("Groups.group_id"))
    invited_user_id = db.Column(db.Integer, db.ForeignKey("Users.user_id"), nullable=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("Users.user_id"), nullable=True)
    email = db.Column(db.String(120))
    phone_number = db.Column(db.String(45))
    status = db.Column(db.String(20), default="pending")  # pending, accepted, rejected
    token = db.Column(db.String(64), unique=True)
    date = db.Column(db.Date, nullable=True)  # Date associated with the invite