import hashlib
import os
from functools import wraps

from flask import request
from pydantic import ValidationError
from werkzeug.exceptions import BadRequest

from api.error_handlers import _make_response


FORTNITE_SERVICE_API_AUTH_DIGEST = os.getenv("FORTNITE_SERVICE_API_AUTH_DIGEST")


def auth(f):
    """ Validate headers in incoming requests for authentication """
    @wraps(f)
    def auth_func(*args, **kwargs):
        # Validate header
        if "API-TOKEN" not in request.headers:
            return _make_response("Authentication header not provided", 400)

        req_api_token = request.headers.get("API-TOKEN", "")
        req_api_digest = hashlib.sha512(req_api_token.encode()).hexdigest()
        if req_api_digest != FORTNITE_SERVICE_API_AUTH_DIGEST:
            return _make_response("Unauthorized", 401)

        return f(*args, **kwargs)
    return auth_func


def parse_payload(payload_model=None):
    """ Validate body in incoming request is a valid JSON and meets
    the Pydantic model, if a model was provided
    """
    def decorator(f):
        @wraps(f)
        def parser(*args, **kwargs):
            # Parse JSON
            try:
                request_body = request.get_json()
                if request_body is None:
                    return _make_response("Missing JSON payload", 400)
            except BadRequest as exc:
                return _make_response(f"Invalid JSON payload: {exc}", 400)

            if payload_model is None:
                kwargs["payload"] = request_body
                return f(*args, **kwargs)

            # Validate schema
            try:
                validated_body = payload_model.model_validate(request_body)
            except ValidationError as exc:
                error_messages = []

                for error in exc.errors():
                    location = ".".join(str(loc) for loc in error["loc"])
                    message = error["msg"]
                    error_messages.append(f"Field '{location}': {message}")

                return _make_response({
                    "error": "Validation failed",
                    "errors": error_messages
                }, 400)

            kwargs["payload"] = validated_body
            return f(*args, **kwargs)
        return parser
    return decorator
