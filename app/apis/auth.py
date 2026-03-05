""" REST API endpoints for authentication and users. """

from flask import request
from flask_restx import Namespace, Resource, fields
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
    @api.response(200, 'User logged in successfully')
    @api.response(400, 'Invalid input or email not registered')
    def post(self):
        """
        Login a user.
        
        Requires an email and a password.
        """
        data = request.json
        required = ['email', 'password']
        missing = [f for f in required if not data.get(f)]
        if missing:
            api.abort(400, f'Missing required fields: {", ".join(missing)}')

        email = data['email'].strip()
        password = data['password'].strip()

        if not email:
            api.abort(400, 'email must not be blank.')
            
        if not password:
            api.abort(400, 'password must not be blank.')

        try:
            user = users_db.get_user_by_email(email)
            if not user:
                api.abort(400, 'Email not registered')
            
            if not users_db.verify_password(user['password'], password):
                api.abort(400, 'Invalid password')
            
            return {'message': 'User logged in successfully', 'user_id': user['id']}, 200
        except ValueError as e:
            api.abort(400, str(e))
