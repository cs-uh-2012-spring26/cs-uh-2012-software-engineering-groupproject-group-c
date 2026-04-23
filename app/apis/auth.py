from flask import request
from flask_restx import Namespace, Resource, fields
import app.services.user_service as user_service

api = Namespace('Authentication', description='Registrations and logins')


# Request models for Swagger UI documentation
register_model = api.model('RegisterInput', {
    'username': fields.String(required=True, example='Ahmed'),
    'email': fields.String(required=True, example='ahmed@gmail.com'),
    'password': fields.String(required=True, example='Ahmed@123'),
    'phone': fields.String(required=True, example='1234567890'),
    'role': fields.String(required=True, example='member')
})

# Define the model for Login
login_model = api.model('LoginInput', {
    'email': fields.String(required=True, example='ahmed@gmail.com'),
    'password': fields.String(required=True, example='Ahmed@123')
})

@api.route('/register')
class Register(Resource):
    @api.expect(register_model)
    @api.response(201, 'User registered successfully')
    @api.response(400, 'Invalid input')
    def post(self):
        """Register a new user account."""
        data = request.json
        
        # Structural check (Fields must exist)
        required = ['username', 'email', 'password', 'phone', 'role']
        if any(not data.get(f) for f in required):
            api.abort(400, "Missing required fields")

        try:
            # Delegate all validation and DB work to the service
            new_user = user_service.register_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                phone=data['phone'],
                role=data['role']
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