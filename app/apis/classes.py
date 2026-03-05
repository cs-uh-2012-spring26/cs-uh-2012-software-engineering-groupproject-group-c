"""
REST API endpoints for fitness class management.
"""
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, set_access_cookies, get_jwt

import app.db.classes as cls_db

api = Namespace('classes', description='Fitness class operations')

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

        for c in classes:
            c.pop("booked_members", None)  

        return {'classes': classes}, 200


@api.route('/<string:class_id>/book')
class BookClass(Resource):

    @jwt_required()
    @api.response(200, 'Booking successful')
    @api.response(400, 'Already booked or class is full')
    @api.response(403, 'Forbidden - member role required')
    @api.response(404, 'Class not found')
    def post(self, class_id):
        """
        Book a spot in a fitness class. Member only.
        """
        claims = get_jwt()

        if claims['role'] != 'member':
            api.abort(403, 'Only members can book a class.')

        member_email = claims['sub'] 
        cls = cls_db.get_class_by_id(class_id)
        if cls is None:
            api.abort(404, 'Class not found.')

        try:
            updated_class = cls_db.book_class(class_id, member_email)
        except ValueError as e:
            api.abort(400, str(e))

        return {
            'message': 'Booking successful.',
            'class_id': class_id,
            'enrolled': updated_class['enrolled'],
            'capacity': updated_class['capacity'],
        }, 200


@api.route('/<string:class_id>/members')
class ClassMembers(Resource):

    @jwt_required()
    @api.response(200, 'Success')
    @api.response(403, 'Forbidden – trainer or admin role required')
    @api.response(404, 'Class not found')
    def get(self, class_id):
        """
        View the list of members who booked a class. Trainer or admin only.
        """
        claims = get_jwt()
        if claims['role'] not in ('trainer', 'admin'):
            api.abort(403, 'Trainer or admin role required.')

        try:
            members = cls_db.get_booked_members(class_id)
        except ValueError as e:
            api.abort(404, str(e))

        return {
            'class_id': class_id,
            'total_booked': len(members),
            'booked_members': members,
        }, 200

@api.route('/<string:class_id>/send-reminder')
class SendReminder(Resource):

    @jwt_required()
    @api.response(200, 'Reminders sent successfully')
    @api.response(403, 'Forbidden – trainer or admin role required')
    @api.response(404, 'Class not found')
    def post(self, class_id):
        """
        Send reminder emails to all members who booked this class.
        Trainer or admin only.

        Returns the email body for each member in the response (for testing/demo purposes).
        """

        # Check role
        claims = get_jwt()
        if claims['role'] not in ('trainer', 'admin'):
            api.abort(403, 'Trainer or admin role required.')

        # Fetch class
        cls = cls_db.get_class_by_id(class_id)
        if cls is None:
            api.abort(404, 'Class not found.')

        # Get booked members
        booked_members = cls.get('booked_members', [])
        if not booked_members:
            return {'message': 'No members booked for this class.'}, 200

        sent_emails = []

        # Construct and “send” email to each booked member
        for member_email in booked_members:
            email_subject = f"Reminder: {cls['name']} on {cls['schedule']}"
            email_body = f"""
Hello {member_email},

This is a reminder for the fitness class you booked:

Class Name: {cls['name']}
Instructor: {cls['instructor']}
Date/Time: {cls['schedule']}
Location: {cls['location']}
Description: {cls.get('description', 'No description')}

See you there!
"""
            # Simulate sending email (print/log)
            print(f"Sending email to {member_email}:\n{email_body}")

            # Collect email info to return in response
            sent_emails.append({
                "to": member_email,
                "subject": email_subject,
                "body": email_body.strip()  # strip extra whitespace
            })

        # Return all emails in the JSON response for testing/demo
        return {
            "message": f"Reminder emails sent to {len(sent_emails)} members.",
            "class_id": class_id,
            "class_name": cls['name'],
            "schedule": cls['schedule'],
            "emails": sent_emails
        }, 200