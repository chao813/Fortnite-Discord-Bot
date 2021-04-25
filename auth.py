import hashlib
import os
from functools import wraps

from flask import request, jsonify
from error_handlers import _make_response

FORTNITE_REPLAY_ELIM_API_AUTH_DIGEST = os.getenv("FORTNITE_REPLAY_ELIM_API_AUTH_DIGEST")

def validate(f):
    """ Validate headers for incoming requests
    """
    @wraps(f)
    def validate(*args, **kwargs):
        # Validate header
        if "API-TOKEN" not in request.headers:
            return _make_response("Authentication header not provided", 400)
        
        req_api_token = request.headers.get("API-TOKEN", "")
        req_api_digest = hashlib.sha512(req_api_token.encode()).hexdigest()
        if req_api_digest != FORTNITE_REPLAY_ELIM_API_AUTH_DIGEST:
            return _make_response("Unauthorized", 401)

        return f(*args, **kwargs)
    return validate

