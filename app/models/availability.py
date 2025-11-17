from app.extensions import db

class Availability(db.Model):
    __tablename__ = "Availability"
    availability_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.user_id"))
    group_id = db.Column(db.Integer, db.ForeignKey("Groups.group_id"))
    calendar_id = db.Column(db.Integer, db.ForeignKey("Calendar.calendar_id"))
    date = db.Column(db.Date)
    status = db.Column(db.String(20), default="pending")  # 'busy', 'available', 'pending'
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
