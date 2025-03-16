from flask import Flask, jsonify, request
from werkzeug.exceptions import BadRequest

from api.auth import validate
from api.error_handlers import initialize_error_handlers
from core.logger import initialize_request_logger


app = Flask(__name__)
initialize_error_handlers(app)
initialize_request_logger(app)


@app.route("/fortnite/healthcheck")
def healthcheck():
    """ API Healthcheck """
    return jsonify({"status": "ok"}), 200


@app.route("/fortnite/replay/elims", methods=["POST"])
@validate
def post():
    """
    POST request Body
        {
            "eliminated_by_me": {},
            "eliminated_me": {}
        }
    """
    try:
        elim_data = request.get_json()
    except BadRequest as exc:
        return jsonify({
            "message": "Invalid JSON payload",
            "error": exc
        }), 400

    global eliminated_by_me_dict
    global eliminated_me_dict
    eliminated_by_me_dict = elim_data["eliminated_by_me"]
    eliminated_me_dict = elim_data["eliminated_me"]

    return jsonify({
        "status": "success",
        "data": {
            "eliminated_by_me": eliminated_by_me_dict,
            "eliminated_me": eliminated_me_dict
        }
    }), 200
