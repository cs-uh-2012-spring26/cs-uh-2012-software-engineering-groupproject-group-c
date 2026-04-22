from functools import wraps
from flask_jwt_extended import get_jwt
from flask_restx import abort

def require_roles(*allowed_roles):
    """
    Decorator to restrict access based on UserRole values.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get('role')
            
            # Check if the user's role is in our allowed list
            # We convert Enum objects to their string values for comparison
            allowed_values = [role.value for role in allowed_roles]
            
            if user_role not in allowed_values:
                abort(403, f"Access denied. Role should be: {allowed_values}")
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator