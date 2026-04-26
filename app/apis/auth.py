from flask import request
from flask_restx import Namespace, Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
import app.services.user_service as user_service
import app.models.input_models as input_models

api = Namespace('Authentication', description='Registrations and logins')

register_model = api.model('RegisterInput', input_models.register_input)

login_model = api.model('LoginInput', input_models.login_input)

preferences_model = api.model('PreferencesInput', input_models.preferences_input)


@api.route('/register')
class Register(Resource):
    @api.expect(register_model, validate=True)
    @api.response(201, 'User registered successfully')
    @api.response(400, 'Invalid input')
    def post(self):
        """Register a new user account."""
        data = request.json

        try:
            new_user = user_service.register_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                phone=data['phone'],
                role=data['role'],
                notification_preferences=data.get('notification_preferences'),
                telegram_chat_id=data.get('telegram_chat_id')
            )
            return {'message': 'User registered successfully', 'user_id': new_user['id']}, 201
        except ValueError as e:
            api.abort(400, str(e))


@api.route('/login')
class Login(Resource):
    @api.expect(login_model, validate=True)
    @api.response(200, 'Login successful')
    @api.response(401, 'Invalid credentials')
    def post(self):
        """Login to receive a JWT token."""
        data = request.json

        auth_result = user_service.authenticate_user(data['email'], data['password'])

        if not auth_result:
            api.abort(401, 'Invalid email or password.')

        return auth_result, 200


@api.route('/preferences')
class NotificationPreferences(Resource):
    @jwt_required()
    @api.expect(preferences_model, validate=True)
    @api.response(200, 'Preferences updated successfully')
    @api.response(400, 'Invalid input')
    def patch(self):
        """Update notification preferences for the logged-in user."""
        email = get_jwt_identity()
        data = request.json

        try:
            updated_user = user_service.update_user_preferences(
                email=email,
                preferences=data['notification_preferences'],
                telegram_chat_id=data.get('telegram_chat_id')
            )
            return {
                'message': 'Preferences updated successfully',
                'notification_preferences': updated_user.get('notification_preferences'),
                'telegram_chat_id': updated_user.get('telegram_chat_id')
            }, 200
        except ValueError as e:
            api.abort(400, str(e))