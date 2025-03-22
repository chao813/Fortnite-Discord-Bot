import asyncio
import logging
from collections import defaultdict

from flask import Flask, jsonify

from api.decorators import auth, parse_payload
from api.error_handlers import initialize_error_handlers
from api.models import FlaskContext, Guild
from api.schemas import SendMessagePayload, GameEliminationPayload
from bot.bot import bot, send_message, player_search
from bot.discord_utils import create_players_killed_desc
from core.config import config
from core.exceptions import DiscordExecutionError
from core.logger import initialize_request_logger


app = Flask(__name__)
initialize_error_handlers(app)
initialize_request_logger(app)

# TODO: Flask needs its own logger
logger = logging.getLogger(__name__)


@app.route("/fortnite/healthcheck")
def healthcheck():
    """API Healthcheck."""
    logger.info("test")
    logger.error("test again")
    return jsonify({"status": "ok"}), 200


@app.route("/fortnite/discord/message", methods=["POST"])
@auth
@parse_payload(SendMessagePayload)
def send_message_in_discord(payload):
    """Send message in Discord channel."""
    message = payload.message

    logger.info("Sending message in Discord: %s", message)

    _execute_discord_command(send_message, message)

    return jsonify({"status": "Message sent"}), 200


@app.route("/fortnite/replay/game", methods=["POST"])
@auth
@parse_payload(GameEliminationPayload)
def track_game_eliminations(payload):
    """Track the final eliminator of each player from the parsed replay file dataset.

    Sample request:
    {
        "game_mode": "HabaneroDuo",
        "killed": {
            "squad_member_1": ["guid1"]
        },
        "killed_by": {
            "squad_member_1": ["guid2"]
        }
    }
    """
    _execute_discord_command(send_message, "**Game Summary from Replay File**")

    # Create mapping of killer to killed players and kill count for each player
    last_killer_of = {player: guids[-1] for player, guids in payload.killed_by.items() if guids}
    killers = defaultdict(lambda: {"total_kills": {}, "last_kills": []})

    for player_name, last_killer in last_killer_of.items():
        killers[last_killer]["last_kills"].append(player_name)

        for killer_guid in set(last_killer_of.values()):
            killed_by_guids = payload.killed_by[player_name]
            if killer_guid in killed_by_guids:
                count = killed_by_guids.count(killer_guid)
                killers[killer_guid]["total_kills"][player_name] = count

    # Execute player search on each last killer
    for killer_guid, victims in killers.items():
        players_killed_desc = create_players_killed_desc(victims)
        logger.info(players_killed_desc)

        _execute_discord_command(
            player_search,
            killer_guid,
            game_mode=payload.game_mode,
            players_killed_desc=players_killed_desc,
            is_guid=True
        )

    return jsonify({
        "status": f"Executed {len(killers)} player_search commands",
        "killers": killers
    }), 200


def _execute_discord_command(func, *args, **kwargs):
    """Schedule Discord command coroutine function in the bot's event loop."""
    # Create fake Discord execution context for Flask
    server_name = config["discord"]["server"]
    flask_ctx = FlaskContext(
        guild=Guild(server_name),
        author="Flask",
        invoked_with=func.name
    )

    try:
        future = asyncio.run_coroutine_threadsafe(
            func(flask_ctx, *args, **kwargs),
            bot.loop
        )
        return future.result(timeout=30)
    except Exception as exc:
        raise DiscordExecutionError(
            f"Failed to execute Discord command !{func.name} with args: {args} and kwargs: {kwargs}"
        ) from exc
