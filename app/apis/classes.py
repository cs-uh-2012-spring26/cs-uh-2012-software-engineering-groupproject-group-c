"""
REST API endpoints for fitness class management.
"""
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, set_access_cookies, get_jwt

import app.db.classes as cls_db

api = Namespace('classes', description='Fitness class operations')

# --------------------------------------------------------------------------- #
# Request / Response models (used by Swagger)
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# Request model (used by Swagger to show expected body)
# --------------------------------------------------------------------------- #
class_input_model = api.model('ClassInput', {
    'name': fields.String(required=True, example='Morning Yoga'),
    'instructor': fields.String(required=True, example='Jane Doe'),
    'schedule': fields.String(required=True, example='2026-03-10T08:00'),
    'capacity': fields.Integer(required=True, example=20),
    'location': fields.String(required=True, example='Studio A'),
    'description': fields.String(required=False, example='A relaxing flow for all levels.'),
})

# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #
@api.route('/')
class ClassList(Resource):

    @jwt_required()
    @api.expect(class_input_model)
    @api.response(201, 'Class created successfully')
    @api.response(400, 'Invalid input')
    @api.response(401, 'Unauthorized')
    def post(self):
        """
        Create a new fitness class.

        Requires a valid Bearer token in the Authorization header.
        All fields except `description` are mandatory.
        """

        claims = get_jwt()

        # Trainer or admin only
        if claims['role'] not in ('trainer', 'admin'):
            api.abort(401, 'Unauthorized')
        
        data = request.json

        # --- Field presence check (belt-and-suspenders on top of validate=True)
        required = ['name', 'instructor', 'schedule', 'capacity', 'location']
        missing = [f for f in required if not data.get(f)]
        if missing:
            api.abort(400, f'Missing required fields: {", ".join(missing)}')

        # --- Type / value validation
        capacity = data.get('capacity')
        if not isinstance(capacity, int) or capacity <= 0:
            api.abort(400, 'capacity must be a positive integer.')

        name = data['name'].strip()
        if not name:
            api.abort(400, 'name must not be blank.')

        try:
            new_class = cls_db.add_class(
                name=name,
                instructor=data['instructor'],
                schedule=data['schedule'],
                capacity=capacity,
                location=data['location'],
                description=data.get('description', ''),
            )
        except ValueError as e:
            api.abort(400, str(e))

        return new_class, 201
    
    @api.response(200, 'Success')
    def get(self):
        """
        Retrieve a list of all fitness classes.
        """
        classes = cls_db.get_all_classes()
        return {'classes': classes}, 200
