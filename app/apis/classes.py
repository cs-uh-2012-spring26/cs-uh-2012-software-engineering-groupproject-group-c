from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
import app.services.class_service as class_service
from app.models.roles import UserRole
from app.models.input_models import (
    class_input,
    recurrence_input,
    update_recurrence_input,
    book_occurrence_input,
    send_reminder_input,
    view_members_input,
)
from app.utils.auth_decorators import require_roles

api = Namespace('classes', description='Fitness class operations')

# --- Input models ---
recurrence_model = api.model('RecurrenceInput', recurrence_input)

class_input_with_recurrence = dict(class_input)
class_input_with_recurrence['recurrence'] = fields.Nested(
    recurrence_model,
    required=False,
    description='Optional recurrence rule for recurring classes',
)
class_input_model = api.model('ClassInput', class_input_with_recurrence)

update_recurrence_model = api.model(
    'UpdateRecurrenceInput', update_recurrence_input
)

book_occurrence_model = api.model(
    'BookOccurrenceInput', book_occurrence_input
)

send_reminder_model = api.model(
    'SendReminderInput', send_reminder_input
)

view_members_model = api.model(
    'ViewMembersInput', view_members_input
)


@api.route('/')
class ClassList(Resource):
    @api.response(200, 'Success')
    def get(self):
        """Retrieve all classes (Public View).

        Every class entry includes an 'occurrence_date' field.
        Recurring classes are expanded into one entry per occurrence.
        Non-recurring classes have a single entry where occurrence_date
        equals the schedule date.
        """
        return {'classes': class_service.get_public_classes()}, 200

    @jwt_required()
    @require_roles(UserRole.ADMIN, UserRole.TRAINER)
    @api.expect(class_input_model, validate=True)
    def post(self):
        """Create a new fitness class (optionally recurring)."""
        try:
            new_class = class_service.create_class(
                name=request.json.get('name'),
                instructor=request.json.get('instructor'),
                schedule=request.json.get('schedule'),
                capacity=request.json.get('capacity'),
                location=request.json.get('location'),
                description=request.json.get('description', ''),
                recurrence=request.json.get('recurrence'),
            )
            return new_class, 201
        except ValueError as e:
            api.abort(400, str(e))


@api.route('/<string:class_id>/book')
class BookClass(Resource):
    @jwt_required()
    @require_roles(UserRole.MEMBER)
    @api.expect(book_occurrence_model, validate=True)
    def post(self, class_id):
        """Book a spot in a specific occurrence (Members Only).

        'occurrence_date' is always required. For non-recurring classes
        use the class schedule date. For recurring classes use a valid
        occurrence date from the public listing.
        """
        member_email = get_jwt_identity()
        occurrence_date = request.json.get('occurrence_date')
        try:
            updated = class_service.book_class_for_member(
                class_id, member_email, occurrence_date=occurrence_date,
            )
            return {
                'message': 'Booking successful.',
                'enrolled': updated['enrolled'],
                'capacity': updated['capacity']
            }, 200
        except ValueError as e:
            api.abort(400, str(e))


@api.route('/<string:class_id>/members')
class ClassMembers(Resource):
    @jwt_required()
    @require_roles(UserRole.ADMIN, UserRole.TRAINER)
    @api.expect(view_members_model)
    def post(self, class_id):
        """View booked members for a class.

        Optionally pass 'occurrence_date' in the body to see who booked
        a specific session. Copy the value from the GET /classes/ listing.

        If omitted, returns all members across all occurrences (deduplicated).

        Example body: {"occurrence_date": "2027-06-01T07:00:00"}
        """
        occurrence_date = None
        body = request.get_json(silent=True)
        if body:
            occurrence_date = body.get('occurrence_date')
        try:
            members = class_service.get_class_members(
                class_id, occurrence_date=occurrence_date,
            )
            response = {'class_id': class_id, 'booked_members': members}
            if occurrence_date:
                response['occurrence_date'] = occurrence_date
            return response, 200
        except ValueError as e:
            return {"message": str(e)}, 404


@api.route('/<string:class_id>/recurrence')
class ClassRecurrence(Resource):
    @jwt_required()
    @require_roles(UserRole.ADMIN, UserRole.TRAINER)
    @api.expect(update_recurrence_model, validate=True)
    def patch(self, class_id):
        """Update the recurrence rule (future occurrences only)."""
        try:
            updated = class_service.update_class_recurrence(
                class_id, request.json,
            )
            return {
                'message': 'Recurrence updated for future occurrences.',
                'class': updated,
            }, 200
        except ValueError as e:
            api.abort(400, str(e))


@api.route('/<string:class_id>/send-reminder')
class SendReminders(Resource):
    @jwt_required()
    @require_roles(UserRole.ADMIN, UserRole.TRAINER)
    @api.expect(send_reminder_model)
    def post(self, class_id):
        """Send reminders to booked members.

        Optionally pass 'occurrence_date' in the body to send reminders
        only to members booked for that specific session. Copy the value
        from the GET /classes/ listing.

        If omitted, sends reminders to all booked members across all sessions.

        Example body: {"occurrence_date": "2027-06-01T07:00:00"}
        """
        occurrence_date = None
        body = request.get_json(silent=True)
        if body:
            occurrence_date = body.get('occurrence_date')
        try:
            results = class_service.send_class_reminders(
                class_id, occurrence_date=occurrence_date,
            )
            return {'message': 'Reminders processed', 'results': results}, 200
        except ValueError as e:
            api.abort(400, str(e))