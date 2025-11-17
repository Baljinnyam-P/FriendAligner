from datetime import datetime, timedelta, date
from app.extensions import db
from app.models import Event, Notification

def test_schedule_and_dispatch_notifications(client, token_factory, group_factory, user_factory):
    group, owner = group_factory()
    token, _ = token_factory(owner)
    headers = {"Authorization": f"Bearer {token}"}
    # create event
    resp = client.post("/api/events/create", json={"group_id": group.group_id, "name": "Meet", "date": date.today().strftime("%Y-%m-%d")}, headers=headers)
    event_id = resp.get_json()["event_id"]
    # schedule reminders
    sched = client.post(f"/api/notifications/event/{event_id}/schedule_reminder", headers=headers)
    assert sched.status_code == 201
    # force scheduled_at to past
    with client.application.app_context():
        notifications = Notification.query.filter_by(event_id=event_id, type="reminder").all()
        for n in notifications:
            n.scheduled_at = datetime.utcnow() - timedelta(minutes=1)
        db.session.commit()
    # dispatch
    dispatch = client.post("/api/notifications/send_due", headers=headers)
    assert dispatch.status_code == 200
    assert dispatch.get_json()["count"] >= 1
