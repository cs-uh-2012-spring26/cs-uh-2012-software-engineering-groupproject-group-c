from app.config import Config
from app.db import DB
from werkzeug.exceptions import HTTPException

from http import HTTPStatus
from flask import Flask
from flask_restx import Api
from flask_jwt_extended import JWTManager  
from app.apis.classes import api as classes_ns  
from app.apis.auth import api as auth_ns

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    DB.init_app(app)
    jwt = JWTManager(app)   

    api = Api(
        title="Fitness Class Management API",
        version="1.0",
        description="API for managing and booking fitness classes.",
        authorizations={                            
            'Bearer': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'Authorization',
                'description': "Enter: Bearer <your_token>",
            }
        },
        security='Bearer',
    )

    api.init_app(app)
    api.add_namespace(classes_ns) 
    api.add_namespace(auth_ns) 

    from flask_jwt_extended.exceptions import JWTExtendedException
    from jwt.exceptions import PyJWTError

    @api.errorhandler(JWTExtendedException)
    def handle_jwt_exceptions(error):
        return {"message": str(error)}, HTTPStatus.BAD_REQUEST

    @api.errorhandler(PyJWTError)
    def handle_pyjwt_exceptions(error):
        return {"message": str(error)}, HTTPStatus.BAD_REQUEST

    @api.errorhandler(Exception)
    def handle_input_validation_error(error):
        if isinstance(error, HTTPException):
            return {"message": getattr(error, 'data', {}).get('message', str(error))}, error.code
        return {"message": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR

    return app
