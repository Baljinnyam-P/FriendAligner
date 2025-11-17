# events.py
from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import Event, Group, User
from ..services.google_places import find_places, get_place_details
events_bp = Blueprint('events', __name__)

# Create event (manual fields)
@events_bp.route('/create', methods=['POST'])
@jwt_required()
def create_event():
    data = request.get_json()
    group_id = data.get('group_id')
    name = data.get('name')
    date_str = data.get('date')
    location_name = data.get('location_name')
    address = data.get('address')
    place_id = data.get('place_id')
    raw_identity = get_jwt_identity()
    try:
        user_id = int(raw_identity)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid token identity'}), 401
    from datetime import datetime
    try:
        event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        return jsonify({'error': 'Invalid date format, expected YYYY-MM-DD'}), 400
    event = Event(group_id=group_id, name=name, date=event_date, location_name=location_name, address=address, place_id=place_id, created_by_user_id=user_id)
    db.session.add(event)
    db.session.commit()
    # Notify group members
    group = db.session.get(Group, group_id)
    member_ids = [group.user_id] if group else []
    if group:
        member_ids += [m.user_id for m in group.members]
        # Notification logic removed
    return jsonify({'message': 'Event created', 'event_id': event.event_id}), 201

# Create event from Google Place selection
@events_bp.route('/create_from_place', methods=['POST'])
@jwt_required()
def create_event_from_place():
    data = request.get_json()
    group_id = data.get('group_id')
    place_id = data.get('place_id')
    date = data.get('date')
    if not group_id or not place_id or not date:
        return jsonify({'error': 'group_id, place_id, date required'}), 400
    try:
        details = get_place_details(place_id)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    raw_identity = get_jwt_identity()
    try:
        user_id = int(raw_identity)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid token identity'}), 401
    event = Event(group_id=group_id,
                  name=details.get('name'),
                  date=date,
                  location_name=details.get('name'),
                  address=details.get('formatted_address'),
                  place_id=place_id,
                  created_by_user_id=user_id)
    db.session.add(event)
    db.session.commit()
    # Notify group members
    group = db.session.get(Group, group_id)
    member_ids = [group.user_id] if group else []
    if group:
        member_ids += [m.user_id for m in group.members]
        # Notification logic removed
    return jsonify({'message': 'Event created from place', 'event_id': event.event_id}), 201

# List events by group
@events_bp.route('/group/<int:group_id>', methods=['GET'])
@jwt_required()
def list_events(group_id):
    events = Event.query.filter_by(group_id=group_id).order_by(Event.date.asc()).all()
    result = [{
        'event_id': e.event_id,
        'name': e.name,
        'date': str(e.date),
        'location_name': e.location_name,
        'address': e.address,
        'finalized': e.finalized
    } for e in events]
    return jsonify(result), 200

# Update event
@events_bp.route('/<int:event_id>', methods=['PUT'])
@jwt_required()
def update_event(event_id):
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    data = request.get_json()
    event.name = data.get('name', event.name)
    date_str = data.get('date')
    if date_str:
        from datetime import datetime
        try:
            event.date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            return jsonify({'error': 'Invalid date format, expected YYYY-MM-DD'}), 400
    event.location_name = data.get('location_name', event.location_name)
    event.address = data.get('address', event.address)
    db.session.commit()
    return jsonify({'message': 'Event updated'}), 200

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

# Finalize event and notify
@events_bp.route('/finalize/<int:event_id>', methods=['POST'])
@jwt_required()
def finalize_event(event_id):
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    event.finalized = True
    db.session.commit()
    # Notify group members
    group = db.session.get(Group, event.group_id)
    member_ids = [group.user_id] if group else []
    if group:
        member_ids += [m.user_id for m in group.members]
    # Notification logic removed
    return jsonify({'message': 'Event finalized'}), 200


# Finder form & results (HTML rendering)
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