from flask import Blueprint, jsonify


healthcheck_bp = Blueprint("healthcheck_api", __name__)


@healthcheck_bp.route("/healthcheck", methods=["GET"])
def healthcheck():
    """ API Healthcheck """
    status = {
        "status": "ok"
    }

    return jsonify(status), 200
