import os

from flask import Blueprint, jsonify, request
from werkzeug.exceptions import BadRequest

from auth import validate
from database.mysql import MySQL


FORTNITE_TEXT_CHANNEL_ID = int(os.getenv("FORTNITE_DISCORD_TEXT_CHANNEL_ID"))

replays_bp = Blueprint("replays_api", __name__)


@replays_bp.route("/fortnite/replay/elims", methods=["POST"])
@validate
async def post():
    """ Updates Discord bot with latest elimination dict
    POST request Body
        {
            "eliminated": {},
            "eliminated_by": {}
        }
    """
    try:
        elim_data = request.get_json()
    except BadRequest as e:
        return jsonify({
            "message": "Invalid JSON payload",
            "error": e
        }), 400

    game_stats = {
        "discord_chat_id": FORTNITE_TEXT_CHANNEL_ID,
        "end_date": "2021-11-12 00:00:00",
        "total_kills": 29,
        "eliminated": elim_data["eliminated"],
        "eliminated_by": elim_data["eliminated_by"]
    }

    mysql = await MySQL.create()
    await mysql.insert_game_record(game_stats)

    return jsonify({
        "status": "success"
    }), 200
