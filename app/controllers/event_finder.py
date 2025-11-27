
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import EventFinder, Group, Calendar
from app.services.google_places import find_places, get_place_details

event_finder_bp = Blueprint('event_finder', __name__)

# Get place details by place_id
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
