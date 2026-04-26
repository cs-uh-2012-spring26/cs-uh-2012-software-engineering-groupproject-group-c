from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
import app.services.user_service as user_service

api = Namespace('Authentication', description='Registrations and logins')

register_model = api.model('RegisterInput', {
    'username': fields.String(required=True, example='Ahmed'),
    'email': fields.String(required=True, example='ahmed@gmail.com'),
    'password': fields.String(required=True, example='Ahmed@123'),
    'phone': fields.String(required=True, example='1234567890'),
    'role': fields.String(required=True, example='member'),
    'notification_preferences': fields.List(
        fields.String,
        required=False,
        example=['email'],
        description="Notification channels: 'email', 'telegram'"
    ),
    'telegram_chat_id': fields.String(
        required=False,
        example='123456789',
        description="Required if telegram is in notification_preferences"
    )
})

login_model = api.model('LoginInput', {
    'email': fields.String(required=True, example='ahmed@gmail.com'),
    'password': fields.String(required=True, example='Ahmed@123')
})

preferences_model = api.model('PreferencesInput', {
    'notification_preferences': fields.List(
        fields.String,
        required=True,
        example=['email', 'telegram'],
        description="Notification channels: 'email', 'telegram'"
    ),
    'telegram_chat_id': fields.String(
        required=False,
        example='123456789',
        description="Required if telegram is in notification_preferences"
    )
})


@api.route('/register')
class Register(Resource):
    @api.expect(register_model)
    @api.response(201, 'User registered successfully')
    @api.response(400, 'Invalid input')
    def post(self):
        """Register a new user account."""
        data = request.json

        required = ['username', 'email', 'password', 'phone', 'role']
        if any(not data.get(f) for f in required):
            api.abort(400, "Missing required fields")

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
    @api.expect(login_model)
    @api.response(200, 'Login successful')
    @api.response(401, 'Invalid credentials')
    def post(self):
        """Login to receive a JWT token."""
        data = request.json
        if not data or not data.get('email') or not data.get('password'):
            api.abort(400, "Email and password required")

        auth_result = user_service.authenticate_user(data['email'], data['password'])

        if not auth_result:
            api.abort(401, 'Invalid email or password.')

        return auth_result, 200


@api.route('/preferences')
class NotificationPreferences(Resource):
    @jwt_required()
    @api.expect(preferences_model)
    @api.response(200, 'Preferences updated successfully')
    @api.response(400, 'Invalid input')
    def patch(self):
        """Update notification preferences for the logged-in user."""
        email = get_jwt_identity()
        data = request.json

        if not data.get('notification_preferences'):
            api.abort(400, "notification_preferences is required")

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