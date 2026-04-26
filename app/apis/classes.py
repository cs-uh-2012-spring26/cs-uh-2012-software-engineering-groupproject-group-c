from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
import app.services.class_service as class_service
from app.models.roles import UserRole
from app.models.input_models import class_input
from app.utils.auth_decorators import require_roles

api = Namespace('classes', description='Fitness class operations')

class_input_model = api.model('ClassInput', class_input)

@api.route('/')
class ClassList(Resource):
    @api.response(200, 'Success')
    def get(self):
        """Retrieve all classes (Public View)."""
        return {'classes': class_service.get_public_classes()}, 200

    @jwt_required()
    @require_roles(UserRole.ADMIN, UserRole.TRAINER)
    @api.expect(class_input_model, validate=True)
    def post(self):
        """Create a new fitness class."""
        try:
            new_class = class_service.create_class(
                name=request.json.get('name'),
                instructor=request.json.get('instructor'),
                schedule=request.json.get('schedule'),
                capacity=request.json.get('capacity'),
                location=request.json.get('location'),
                description=request.json.get('description', '')
            )
            return new_class, 201
        except ValueError as e:
            api.abort(400, str(e))

@api.route('/<string:class_id>/book')
class BookClass(Resource):
    @jwt_required()
    @require_roles(UserRole.MEMBER)
    def post(self, class_id):
        """Book a spot (Members Only)."""
        member_email = get_jwt_identity()
        try:
            updated = class_service.book_class_for_member(class_id, member_email)
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
    def get(self, class_id):
        """View member list."""
        try:
            members = class_service.get_class_members(class_id)
            return {'class_id': class_id, 'booked_members': members}, 200
        except ValueError as e:
            return {"message": str(e)}, 404

@api.route('/<string:class_id>/send-reminder')
class SendReminders(Resource):
    @jwt_required()
    @require_roles(UserRole.ADMIN, UserRole.TRAINER)
    def post(self, class_id):
        """Send emails to all members."""
        try:
            results = class_service.send_class_reminders(class_id)
            return {'message': 'Reminders processed', 'results': results}, 200
        except ValueError as e:
            api.abort(400, str(e))