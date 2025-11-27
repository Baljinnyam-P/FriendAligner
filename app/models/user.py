from app.extensions import db

from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = "Users"
    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(45), unique=True)
    password = db.Column(db.String(255))
    first_name = db.Column(db.String(45))
    last_name = db.Column(db.String(45))
    phone_number = db.Column(db.String(45), unique=True)
    is_admin = db.Column(db.Boolean, default=False)
    availabilities = db.relationship("Availability", backref="user")
    groups = db.relationship("Group", backref="owner", overlaps="organized_groups,owner")
    group_memberships = db.relationship("GroupMember", backref="user_link", overlaps="group_member_links,user_link")

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)