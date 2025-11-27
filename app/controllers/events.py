
# events.py
from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import Event, Group, User
from datetime import datetime
from ..services.google_places import find_places, get_place_details
events_bp = Blueprint('events', __name__)


# Create event from Google Place selection
#Called from the event finder results page
@events_bp.route('/create_from_place', methods=['POST'])
@jwt_required()
def create_event_from_place():
    data = request.get_json()
    place_id = data.get('place_id')
    date = data.get('date')
    start_time_str = data.get('start_time')
    end_time_str = data.get('end_time')
    raw_identity = get_jwt_identity()
    try:
        user_id = int(raw_identity)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid token identity'}), 401
    # Support both group and personal calendar
    group_id = data.get('group_id')
    calendar_id = data.get('calendar_id')
    calendar_type = data.get('calendar_type', 'group')
    if calendar_type == 'personal':
        if not calendar_id or not place_id or not date:
            return jsonify({'error': 'calendar_id, place_id, date required'}), 400
        try:
            details = get_place_details(place_id)
        except Exception as e:
            return jsonify({'error': str(e)}), 400
        event_name = details.get('name')
        event_date = date
        address = details.get('formatted_address')
        location_name = details.get('name')
        description = details.get('types') and ', '.join(details.get('types')) or None
        photos = details.get('photos')
        image_url = None
        api_key = current_app.config.get("GOOGLE_PLACES_API_KEY")
        if isinstance(photos, list) and photos and api_key:
            photo_reference = photos[0]
            image_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={api_key}"
        google_maps_url = f"https://www.google.com/maps/search/?api=1&query={address.replace(' ', '+')}" if address else None
        try:
            start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M") if start_time_str else None
            end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M") if end_time_str else None
        except Exception:
            start_time = None
            end_time = None
        # Build Google Maps Place URL
        place_url = f"https://www.google.com/maps/place/?q=place_id:{details.get('place_id')}" if details.get('place_id') else None
        event = Event(
            calendar_id=calendar_id,
            group_id=None,
            name=event_name,
            description=description,
            date=event_date,
            start_time=start_time,
            end_time=end_time,
            location_name=location_name,
            address=address,
            image_url=image_url,
            google_maps_url=google_maps_url,
            created_by_user_id=user_id,
            finalized=False,
            place_url=place_url
        )
        db.session.add(event)
        db.session.commit()
        return jsonify({'message': 'Event added to personal calendar', 'event_id': event.event_id}), 201
    #For group shared calendar
    else:
        if not group_id or not place_id or not date:
            return jsonify({'error': 'group_id, place_id, date required'}), 400
        try:
            details = get_place_details(place_id)
        except Exception as e:
            return jsonify({'error': str(e)}), 400
        # Members can suggest events; only organizer can finalize
        is_organizer = False
        group = db.session.get(Group, group_id)
        if group and user_id == group.organizer_id:
            is_organizer = True
        #This url for building Google Maps Place URL
        place_url = f"https://www.google.com/maps/place/?q=place_id:{details.get('place_id')}" if details.get('place_id') else None
        photos = details.get('photos')
        image_url = None
        api_key = current_app.config.get("GOOGLE_PLACES_API_KEY")
        if isinstance(photos, list) and photos and api_key:
            photo_reference = photos[0]
            # This url for getting the photo from Google Places API
            image_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={api_key}"
        event = Event(
            calendar_id=calendar_id,
            group_id=group_id,
            name=details.get('name'),
            description=details.get('types') and ', '.join(details.get('types')) or None,
            date=date,
            start_time=None,
            end_time=None,
            location_name=details.get('name'),
            address=details.get('formatted_address'),
            image_url=image_url,
            # This url for going to google maps with the address
            google_maps_url=f"https://www.google.com/maps/search/?api=1&query={details.get('formatted_address').replace(' ', '+')}" if details.get('formatted_address') else None,
            created_by_user_id=user_id,
            finalized=is_organizer,
            place_url=place_url
        )
        db.session.add(event)
        db.session.commit()
        # Notify group members
        group = db.session.get(Group, group_id)
        member_ids = [group.organizer_id] if group else []
        if group:
            member_ids += [m.user_id for m in group.members]
            # Notification logic removed
        return jsonify({'message': 'Event created from place', 'event_id': event.event_id}), 201

#For Future Use
# List events by group
@events_bp.route('/group/<int:group_id>', methods=['GET'])
@jwt_required()
def list_events(group_id):
    events = Event.query.filter_by(group_id=group_id).order_by(Event.date.asc()).all()
    result = [{
        'event_id': e.event_id,
        'calendar_id': e.calendar_id,
        'group_id': e.group_id,
        'name': e.name,
        'description': e.description,
        'date': str(e.date),
        'start_time': e.start_time.strftime('%Y-%m-%d %H:%M') if e.start_time else None,
        'end_time': e.end_time.strftime('%Y-%m-%d %H:%M') if e.end_time else None,
        'location_name': e.location_name,
        'address': e.address,
        'image_url': e.image_url,
        'google_maps_url': e.google_maps_url,
        'place_url': getattr(e, 'place_url', None),
        'finalized': e.finalized
    } for e in events]
    return jsonify(result), 200


# Delete event
@events_bp.route('/<int:event_id>', methods=['DELETE'])
@jwt_required()
def delete_event(event_id):
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    db.session.delete(event)
    db.session.commit()
    return jsonify({'message': 'Event deleted'}), 200

# Remove event from personal calendar 
@events_bp.route('/remove_personal_event/<int:availability_id>', methods=['DELETE'])
def remove_personal_event(availability_id):
    from app.models import Availability
    availability = Availability.query.get(availability_id)
    if not availability or availability.status != 'event':
        return jsonify({'error': 'Event not found in personal calendar'}), 404
    db.session.delete(availability)
    db.session.commit()
    return jsonify({'message': 'Event removed from personal calendar'}), 200


#Not used for now
# Finalize event and notify
@events_bp.route('/finalize/<int:event_id>', methods=['POST'])
@jwt_required()
def finalize_event(event_id):
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    group = db.session.get(Group, event.group_id)
    raw_identity = get_jwt_identity()
    try:
        user_id = int(raw_identity)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid token identity'}), 401
    if not group or user_id != group.organizer_id:
        return jsonify({'error': 'Only organizer can finalize events'}), 403
    event.finalized = True
    db.session.commit()

    # Notify group members (excluding the organizer who finalized)
    member_ids = [m.user_id for m in group.members]
    if group.organizer_id not in member_ids:
        member_ids.append(group.organizer_id)
    from app.models import Notification, User
    from flask import current_app
    import smtplib
    from email.mime.text import MIMEText
    for uid in member_ids:
        if uid == user_id:
            continue  # Skip the organizer who finalized
        notif_msg = f"Event '{event.name}' has been finalized for group '{group.group_name}' on {event.date}."
        notification = Notification(user_id=uid, message=notif_msg, type='event_finalized')
        db.session.add(notification)
        # Send email if user has email
        member = db.session.get(User, uid)
        if member and member.email:
            subject = "Event Finalized Notification"
            body = notif_msg
            smtp_server = current_app.config.get('SMTP_SERVER')
            smtp_port = current_app.config.get('SMTP_PORT')
            smtp_user = current_app.config.get('SMTP_USER')
            smtp_password = current_app.config.get('SMTP_PASSWORD')
            from_email = smtp_user
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = from_email
            msg['To'] = member.email
            try:
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.sendmail(from_email, [member.email], msg.as_string())
            except Exception as e:
                print(f"Email send failed: {e}")
    db.session.commit()
    return jsonify({'message': 'Event finalized and members notified'}), 200


# Finder form & results (for rendering event finder results page)
@events_bp.route("/find", methods=["GET"])
def find_event():
    """
    Renders event results page with Google Maps and places list.
    Example: /api/events/find?zip=10001&keyword=coffee
    """
    zip_code = request.args.get("zip")
    keyword = request.args.get("keyword")
    max_results = int(request.args.get("max", 10))

    # if missing params, redirect back to form
    if not zip_code or not keyword:
        return redirect(url_for("events.event_finder_form"))

    try:
        results = find_places(zip_code, keyword, max_results=20)  # get more, then filter
        # Sort and limit to top 5 by rating
        top_results = sorted(results, key=lambda x: x.get("rating") or 0, reverse=True)[:5]
        api_key = current_app.config.get("GOOGLE_PLACES_API_KEY")
        return render_template("event_finder_results.html", results=top_results, maps_api_key=api_key)
    except Exception as e:
        current_app.logger.exception("Error fetching places")
        return render_template("event_finder.html", error=str(e)), 500


@events_bp.route("/form", methods=["GET"])
def event_finder_form():
    """Render the search form where user inputs ZIP + keyword."""
    return render_template("event_finder.html")


@events_bp.route("/", methods=["GET"])
def root_redirect():
    return redirect(url_for("events.event_finder_form"))





#Not used for now
# Update event
@events_bp.route('/<int:event_id>', methods=['PUT'])
@jwt_required()
def update_event(event_id):
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    data = request.get_json()
    event.name = data.get('name', event.name)
    event.description = data.get('description', event.description)
    date_str = data.get('date')
    start_time_str = data.get('start_time')
    end_time_str = data.get('end_time')
    if date_str:
        from datetime import datetime
        try:
            event.date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            return jsonify({'error': 'Invalid date format, expected YYYY-MM-DD'}), 400
    if start_time_str:
        try:
            event.start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M")
        except Exception:
            return jsonify({'error': 'Invalid start_time format, expected YYYY-MM-DD HH:MM'}), 400
    if end_time_str:
        try:
            event.end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M")
        except Exception:
            return jsonify({'error': 'Invalid end_time format, expected YYYY-MM-DD HH:MM'}), 400
    event.location_name = data.get('location_name', event.location_name)
    event.address = data.get('address', event.address)
    event.image_url = data.get('image_url', event.image_url)
    event.google_maps_url = data.get('google_maps_url', event.google_maps_url)
    db.session.commit()
    return jsonify({'message': 'Event updated'}), 200