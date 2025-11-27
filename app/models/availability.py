from app.extensions import db

class Availability(db.Model):
    __tablename__ = "Availability"
    availability_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.user_id"), nullable=False)
    calendar_id = db.Column(db.Integer, db.ForeignKey("Calendar.calendar_id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(32), nullable=False)  # 'busy', 'available', 'not sure'
    # Additional field for description
    description = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

