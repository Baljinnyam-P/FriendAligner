from app.extensions import db

class Calendar(db.Model):
    __tablename__ = "Calendar"
    calendar_id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.Float)
    date = db.Column(db.Date)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.user_id"))
    name = db.Column(db.String(100))
    availabilities = db.relationship("Availability", backref="calendar")
