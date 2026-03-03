
from app.config import Config
from app.db import DB

from http import HTTPStatus
from flask import Flask
from flask_restx import Api
from flask_jwt_extended import JWTManager  
from app.apis.classes import api as classes_ns  
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    DB.init_app(app)
    JWTManager(app)   

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

    @api.errorhandler(Exception)
    def handle_input_validation_error(error):
        return {"message": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR

    return app
