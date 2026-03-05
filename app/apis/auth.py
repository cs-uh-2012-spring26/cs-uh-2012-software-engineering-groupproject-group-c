""" REST API endpoints for authentication and users. """

from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, set_access_cookies
import re
import app.db.users as users_db

def is_strong_password(password):
    return (
        len(password) >= 8 and
        re.search(r"[A-Z]", password) and
        re.search(r"[a-z]", password) and
        re.search(r"[0-9]", password)
)

api = Namespace('Authentication', description='Registrations and logins')

# --------------------------------------------------------------------------- #
# Request / Response models
# --------------------------------------------------------------------------- #
register_input_model = api.model('RegisterInput', {
    'username': fields.String(required=True, example='Ahmed'),
    'email': fields.String(required=True, example='ahmed@gmail.com'),
    'password': fields.String(required=True, example='Ahmed@123'),
    'phone': fields.String(required=True, example='1234567890'),
    'role': fields.String(required=True, example='Member', enum=['Admin', 'Member', 'Trainer'])    
})

login_input_model = api.model('LoginInput', {
    'email': fields.String(required=True),
    'password': fields.String(required=True)
})


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #

@api.route('/register')
class Register(Resource):

    @api.expect(register_input_model)
    @api.response(201, 'User registered successfully')
    @api.response(400, 'Invalid input or email already exists')
    def post(self):
        """
        Register a new user account.
        
        Requires a username, a valid email, a password, a phone number, and a role.
        """
        data = request.json
        required = ['username', 'email', 'password', 'phone', 'role']
        missing = [f for f in required if not data.get(f)]
        if missing:
            api.abort(400, f'Missing required fields: {", ".join(missing)}')

        username = data['username'].strip()
        email = data['email'].strip()
        password = data['password'].strip()
        phone = data['phone'].strip()
        role = data['role'].strip()

        if not username:
            api.abort(400, 'username must not be blank.')
            
        if not is_strong_password(password):
            api.abort(400, 'password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, and one number.')

        if not re.match(r'^\d{10}$', phone):
            api.abort(400, 'Invalid phone number format. Must be 10 digits.')

        if role not in ['Admin', 'Member', 'Trainer']:
            api.abort(400, 'Invalid role. Must be one of: Admin, Member, Trainer.')

        if users_db.get_user_by_email(data['email']):
            api.abort(400, "Email already registered")

        try:
            new_user = users_db.add_user(
                username=username,
                email=email,
                password=password,
                role=role,
                phone=phone
            )
            return {'message': 'User registered successfully', 'user_id': new_user['id']}, 201
        except ValueError as e:
            api.abort(400, str(e))



@api.route('/login')
class Login(Resource):

    @api.expect(login_input_model)
    @api.response(200, 'Login successful')
    @api.response(400, 'Missing required fields')
    @api.response(401, 'Invalid credentials')
    def post(self):
        """Login and receive a JWT token. Use it as: Bearer <token>."""
        data = request.json

        missing = [f for f in ['email', 'password'] if not data.get(f)]
        if missing:
            api.abort(400, f'Missing required fields: {", ".join(missing)}')

        user = users_db.get_user_for_login(data['email'])

        # Deliberately vague — don't reveal which part was wrong
        if user is None or not users_db.verify_password(user['password'], data['password']):
            api.abort(401, 'Invalid email or password.')

        # Role is stored as an additional claim inside the token
        token = create_access_token(
            identity=user['id'],
            additional_claims={'role': user['role']}
        )

        return {'token': token, 'role': user['role']}, 200