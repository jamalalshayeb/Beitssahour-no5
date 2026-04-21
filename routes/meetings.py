"""Meeting management module — public stub.

The full implementation (board/committee scheduling, agendas, minutes, RSVP,
attachments) is pending product details from the user. This stub keeps the
route live and visible in navigation so the surface is discoverable.
"""
from flask import Blueprint, render_template
from models import MeetingBody, Meeting

meetings_bp = Blueprint('meetings', __name__)


@meetings_bp.route('/')
def index():
    bodies = MeetingBody.query.filter_by(is_active=True).all()
    upcoming = (Meeting.query
                .filter(Meeting.status == 'scheduled')
                .order_by(Meeting.scheduled_at.asc())
                .limit(10)
                .all())
    return render_template('meetings/index.html', bodies=bodies, upcoming=upcoming)
