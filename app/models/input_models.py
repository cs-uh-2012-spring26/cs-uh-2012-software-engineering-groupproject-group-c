from flask_restx import fields

register_input = {
    'username': fields.String(required=True, example='Ahmed'),
    'email': fields.String(required=True, example='ahmed@gmail.com'),
    'password': fields.String(required=True, example='Ahmed@123'),
    'phone': fields.String(required=True, example='1234567890'),
    'role': fields.String(required=True, example='member'),
    'notification_preferences': fields.List(
        fields.String,
        required=True,
        example=['email'],
        description="Notification channels: 'email', 'telegram'"
    ),
    'telegram_chat_id': fields.String(
        required=False,
        example='123456789',
        description="Required if telegram is in notification_preferences"
    )
}


login_input = {
    'email': fields.String(required=True, example='ahmed@gmail.com'),
    'password': fields.String(required=True, example='Ahmed@123')
}


preferences_input = {
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
}



class_input = {
    'name': fields.String(required=True, example='Morning Yoga'),
    'instructor': fields.String(required=True, example='Jane Doe'),
    'schedule': fields.String(required=True, example='2026-03-10T08:00'),
    'capacity': fields.Integer(required=True, example=20),
    'location': fields.String(required=True, example='Studio A'),
    'description': fields.String(required=False, example='A relaxing flow for all levels.'),
}