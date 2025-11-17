from datetime import datetime
from app.extensions import db

class ChatMessage(db.Model):
    __tablename__ = "ChatMessages"
    message_id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("Groups.group_id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.user_id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="chat_messages")
    group = db.relationship("Group", backref="chat_messages")
