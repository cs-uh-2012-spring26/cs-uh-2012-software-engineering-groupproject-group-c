import pytest
import os

# 1. Force environment variables BEFORE importing the app
os.environ['MONGO_URI'] = "mongodb://localhost:27017"
os.environ['DB_NAME'] = "fitness_test_db"
os.environ['MOCK_DB'] = "true" 
os.environ['DEBUG'] = "true"
os.environ['JWT_SECRET_KEY'] = "super-secret-test-key"

from app import create_app
from app.db import DB
from app.db.constants import CLASS_COLLECTION, BOOKING_COLLECTION, USER_COLLECTION

@pytest.fixture(scope="session")
def app():
    """Create and configure a new app instance for the test session."""
    app = create_app()
    app.config.update({"TESTING": True})
    yield app

@pytest.fixture()
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture(autouse=True)
def clear_db(app):
    """Clear the mock database before EVERY test for complete isolation."""
    DB.get_collection(USER_COLLECTION).delete_many({})
    DB.get_collection(CLASS_COLLECTION).delete_many({})
    DB.get_collection(BOOKING_COLLECTION).delete_many({})
    yield