
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import EventFinder, Group, Calendar
from app.services.google_places import find_places, get_place_details

event_finder_bp = Blueprint('event_finder', __name__)

@event_finder_bp.route('/place_details', methods=['GET'])
def place_details():
    place_id = request.args.get('place_id')
    if not place_id:
        return jsonify({'error': 'Missing place_id'}), 400
    try:
        details = get_place_details(place_id)
        return jsonify({'details': details}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@event_finder_bp.route('/event_finder/search', methods=['POST'])
@jwt_required()
def search_events():
    data = request.get_json()
    zip_code = data.get('zip_code')
    keyword = data.get('keyword', 'event')
    max_results = data.get('max_results', 10)
    try:
        results = find_places(zip_code, keyword, max_results)
        return jsonify({'results': results}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@event_finder_bp.route('/event_finder', methods=['POST'])
@jwt_required()
def create_event_finder():
    data = request.get_json()
    group_id = data.get('group_id')
    calendar_id = data.get('calendar_id')
    zip_code = data.get('zip_code')
    # Validate group and calendar
    group = db.session.get(Group, group_id)
    calendar = db.session.get(Calendar, calendar_id)
    if not group or not calendar:
        return jsonify({'error': 'Group or Calendar not found'}), 404
    event_finder = EventFinder(group_id=group_id, calendar_id=calendar_id, zip_code=zip_code)
    db.session.add(event_finder)
    db.session.commit()
    return jsonify({'message': 'EventFinder record created', 'eventFinder_id': event_finder.eventFinder_id}), 201

@event_finder_bp.route('/event_finder/<int:eventFinder_id>', methods=['GET'])
@jwt_required()
def get_event_finder(eventFinder_id):
    event_finder = db.session.get(EventFinder, eventFinder_id)
    if not event_finder:
        return jsonify({'error': 'EventFinder not found'}), 404
    return jsonify({
        'eventFinder_id': event_finder.eventFinder_id,
        'group_id': event_finder.group_id,
        'calendar_id': event_finder.calendar_id,
        'zip_code': event_finder.zip_code
    }), 200
