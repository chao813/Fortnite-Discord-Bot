from flask import jsonify


def not_found(error):
    """ 404 not found """
    return _make_response(
        "The requested resource was not found", 404)


def method_not_allowed(error):
    """ 405 method not allowed """
    return _make_response(
        "This method is not allowed on the requested resource", 405)


def internal_server_error(error):
    """ 500 internal server error """
    return _make_response(
        "Internal server error", 500)


def _make_response(message, status_code):
    """ Construct json response with status code """
    return jsonify({
        "error": message
    }), status_code


def initialize_error_handlers(app):
    """ Initialize error handlers """
    app.register_error_handler(404, not_found)
    app.register_error_handler(405, method_not_allowed)
    app.register_error_handler(500, internal_server_error)
