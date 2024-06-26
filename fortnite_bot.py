from dotenv import load_dotenv
load_dotenv()


import asyncio
import os
import ast
from functools import partial
from threading import Thread

import discord
from discord.ext.commands import Bot, CommandNotFound
from flask import Flask, jsonify, request
from werkzeug.exceptions import BadRequest

import clients.fortnite_api as fortnite_api
import clients.interactions as interactions
import clients.openai as openai
import clients.stats as stats
import commands
from auth import validate
from error_handlers import initialize_error_handlers
from exceptions import NoSeasonDataError, UserDoesNotExist, UserStatisticsNotFound
from logger import initialize_request_logger, configure_logger, get_logger_with_context, log_command


DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
ACTIVE_PLAYERS_LIST = []
SQUAD_PLAYERS_LIST = os.getenv("SQUAD_PLAYERS_LIST").split(",")
FORTNITE_DISCORD_ROLE_USERS_DICT = ast.literal_eval(str(os.getenv("FORTNITE_DISCORD_ROLE_USERS_DICT")))

logger = configure_logger()

# TODO: Explicitly enable the required privileged intents
#       then change: intents = discord.Intents.all()
intents = discord.Intents.default()
bot = Bot(command_prefix="!", intents=intents)

app = Flask(__name__)
initialize_error_handlers(app)
initialize_request_logger(app)

openai.initialize()

eliminated_by_me_dict = None
eliminated_me_dict = None


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


@bot.event
async def on_ready():
    """ Event handler to setup logger on load """
    logger = get_logger_with_context(identifier="Main")
    logger.info("Started up %s", bot.user.name)
    logger.info("Bot running on servers: %s",
                ", ".join([guild.name for guild in bot.guilds]))


@bot.event
async def on_command_error(ctx, error):
    command = ctx.invoked_with
    if isinstance(error, CommandNotFound):
        logger = get_logger_with_context(identifier="Main")
        logger.warning("Invalid command: %s", command)
        await ctx.send(f"Command `!{command}` does not exist. Use `!list` to see available commands.")


@bot.event
async def on_guild_join(guild):
    """ Event handler to log when the bot joins a new server """
    logger = get_logger_with_context(identifier="Main")
    logger.info("Bot added to new server! Server name: %s", guild.name)


@bot.event
async def on_voice_state_update(member, before, after):
    """ Event handler to track squad stats on voice channel join """
    logger = get_logger_with_context(identifier="Main")
    logger.info("Voice channel update detected for member: %s (channel before: %s, channel after: %s)",
                member.display_name, before.channel, after.channel)

    try:
        if interactions.should_add_player_to_squad_player_session_list(member, before, after):
            if member.display_name in FORTNITE_DISCORD_ROLE_USERS_DICT:
                if FORTNITE_DISCORD_ROLE_USERS_DICT[member.display_name] not in ACTIVE_PLAYERS_LIST:
                    ACTIVE_PLAYERS_LIST.append(FORTNITE_DISCORD_ROLE_USERS_DICT[member.display_name])

        if interactions.should_remove_player_from_squad_player_session_list(member, before, after):
            if member.display_name in FORTNITE_DISCORD_ROLE_USERS_DICT:
                if FORTNITE_DISCORD_ROLE_USERS_DICT[member.display_name] in ACTIVE_PLAYERS_LIST:
                    ACTIVE_PLAYERS_LIST.remove(FORTNITE_DISCORD_ROLE_USERS_DICT[member.display_name])


        if not interactions.send_track_question(member, before, after):
            return
    except Exception as exc:
        logger.warning("Failed to run on_voice_state_update: %s", repr(exc), exc_info=True)
        ACTIVE_PLAYERS_LIST.clear()

    ctx, silent = await interactions.send_track_question_and_wait(
        bot,
        member.display_name)

    await track(ctx, silent)


@bot.command(name=commands.HELP_COMMAND,
             help=commands.HELP_DESCRIPTION,
             aliases=commands.HELP_ALIASES)
@log_command
async def help_manual(ctx):
    """ Lists available commands """
    await interactions.send_commands_list(ctx)


@bot.command(name=commands.PLAYER_SEARCH_COMMAND,
             help=commands.PLAYER_SEARCH_DESCRIPTION,
             aliases=commands.PLAYER_SEARCH_ALIASES)
async def player_search(ctx, *player_name, guid=False, silent=False):
    """ Searches for a player's stats, output to Discord, and log in database """
    player_name = " ".join(player_name)

    # TODO: Parse guid for replays
    # TODO: Change guid to is_guid

    logger = get_logger_with_context(ctx)
    logger.info("Searching for player stats: %s", player_name)

    if not player_name:
        await ctx.send("Please specify an Epic username after the command, "
                       "ex: `!hunted LigmaBalls12`")
        return

    try:
        await fortnite_api.get_player_stats(ctx, player_name, silent)
        if not silent:
            logger.info("Returned player statistics for: %s", player_name)
    except (NoSeasonDataError, UserDoesNotExist, UserStatisticsNotFound) as exc:
        logger.warning("Unable to retrieve statistics for '%s': %s", player_name, exc)
        await ctx.send(exc)
    except Exception as exc:
        error_msg = f"Failed to retrieve player statistics: {repr(exc)}"
        logger.error(error_msg, exc_info=_should_log_traceback(exc))
        await ctx.send(error_msg)


@bot.command(name=commands.TRACK_COMMAND,
             help=commands.TRACK_DESCRIPTION,
             aliases=commands.TRACK_ALIASES)
@log_command
async def track(ctx, silent=False):
    """ Tracks and logs the current stats of the current players """
    logger = get_logger_with_context(ctx)
    if not (players_list := ACTIVE_PLAYERS_LIST):
        players_list = SQUAD_PLAYERS_LIST
        logger.info("No players active on Discord, tracking all squad players instead")
    tasks = [player_search(ctx, username, guid=False, silent=silent) for username in players_list]
    await asyncio.gather(*tasks)


@bot.command(name=commands.UPGRADE_COMMAND,
             help=commands.UPGRADE_DESCRIPTION,
             aliases=commands.UPGRADE_ALIASES)
@log_command
async def upgrade(ctx):
    """ Show map of upgrade locations """
    await interactions.send_upgrade_locations(ctx)


@bot.command(name=commands.HIRE_COMMAND,
             help=commands.HIRE_DESCRIPTION)
@log_command
async def hire(ctx):
    """ Show map of hireable NPC locations """
    await interactions.send_hirable_npc_locations(ctx)


@bot.command(name=commands.CHESTS_COMMAND,
             help=commands.CHESTS_DESCRIPTION,
             aliases=commands.CHESTS_ALIASES)
@log_command
async def chests(ctx):
    """ Show map of bunker and regular chest locations """
    await interactions.send_chest_locations(ctx)


@bot.command(name=commands.STATS_COMMAND,
             help=commands.STATS_DESCRIPTION)
@log_command
async def stats_operations(ctx, *params):
    """ Outputs stats based on the parameters provided.
    Valid options are:
        1. Stats diff of the squad players today
        2. Average stats of the players faced today
    """
    logger = get_logger_with_context(ctx)
    params = list(params)

    command = params.pop(0) if params else None
    if not command:
        message = "Please specify a command, ex: `!stats diff` or `!stats played`"
        logger.warning(message)
        await ctx.send(message)
        return

    usernames = params or ACTIVE_PLAYERS_LIST

    if command in commands.STATS_DIFF_COMMANDS:
        logger.info(f"Querying stats diff today for {', '.join(usernames)}")
        await _stats_diff_today(ctx, usernames)
    elif command in commands.STATS_OPPONENTS_COMMANDS:
        logger.info("Querying opponent stats today")
        await _opponent_stats_today(ctx)
    else:
        await ctx.send(f"Command provided '{command}' is not valid")


async def _stats_diff_today(ctx, usernames):
    """ Outputs the stats diff of the squad players today.
    Perform a silent update of the player stats in the database first
    """
    update_tasks = []
    calculate_tasks = []

    for username in usernames:
        update_tasks.append(player_search(ctx, username, guid=False, silent=True))
        calculate_tasks.append(stats.send_stats_diff_today(ctx, username))

    await asyncio.gather(*update_tasks)
    await asyncio.gather(*calculate_tasks)


async def _opponent_stats_today(ctx):
    """ Outputs the stats of the players faced today """
    await stats.send_opponent_stats_today(ctx)


@bot.command(name=commands.REPLAYS_COMMAND,
             help=commands.REPLAYS_DESCRIPTION)
@log_command
async def replays_operations(ctx, *params):
    """ Outputs replays stats based on the command provided.
    Valid options are:
        1. killed/elims - show stats of players that we eliminated
        2. log - log to db
        3. show stats of players that eliminated us
    """

    logger = get_logger_with_context(ctx)
    params = list(params)

    global eliminated_by_me_dict
    global eliminated_me_dict
    if not eliminated_me_dict and not eliminated_by_me_dict:
        await ctx.send("No replay file found")
        return

    command = None
    username = None
    if len(params) == 2:
        username = params.pop(1)
        command = params.pop(0)
        if username not in ACTIVE_PLAYERS_LIST:
            await ctx.send(f"{username} provided is not a valid squad player")
            return
    if len(params) == 1:
        if params[0] in ACTIVE_PLAYERS_LIST:
            username = params.pop(0)
        else:
            command = params.pop(0)


    if command in commands.REPLAYS_ELIMINATED_COMMANDS:
        logger.info("Outputting players that got eliminated by us")
        await _output_replay_eliminated_by_me_stats_message(ctx, eliminated_by_me_dict, username, silent=False)
    elif command in commands.REPLAYS_LOG_COMMANDS:
        logger.info("Silent logging players that got eliminated by us and eliminated us")
        await _output_replay_eliminated_me_stats_message(ctx, eliminated_me_dict, username, silent=True)
        await _output_replay_eliminated_by_me_stats_message(ctx, eliminated_by_me_dict, username, silent=True)
    else:
        if not command:
            logger.info("Outputting players that eliminated us")
            await _output_replay_eliminated_me_stats_message(ctx, eliminated_me_dict, username, silent=False)
        elif command != commands.REPLAYS_COMMAND and \
                command not in commands.REPLAYS_ELIMINATED_COMMANDS and \
                command not in commands.REPLAYS_LOG_COMMANDS:
            await ctx.send(f"Command provided '{command}' is not valid")
        else:
            await ctx.send(f"{command} left the channel")


async def _output_replay_eliminated_me_stats_message(ctx, eliminated_me_dict, username, silent):
    """ Create Discord Message for the stats of the opponents that eliminated us"""
    for player_guid in eliminated_me_dict:
        squad_players_eliminated_by_player = ""
        send_output = False
        if username == None:
            for squad_player in eliminated_me_dict[player_guid]:
                squad_players_eliminated_by_player += squad_player + ", "
            send_output = True
        if username in eliminated_me_dict[player_guid]:
            squad_players_eliminated_by_player = username + ", "
            send_output = True

        if send_output:
            if not silent:
                await ctx.send(f"Eliminated {squad_players_eliminated_by_player[:-2]}")
            await player_search(ctx, player_guid, guid=True, silent=silent)


async def _output_replay_eliminated_by_me_stats_message(ctx, eliminated_by_me_dict, username, silent):
    """ Create Discord Message for the stats of the opponents that got eliminated by us"""
    if username:
        eliminated_by_me_dict = {username: eliminated_by_me_dict[username]}
    for squad_player in eliminated_by_me_dict:
        if not silent:
            await ctx.send(f"{squad_player} eliminated")
        for player_guid in eliminated_by_me_dict[squad_player]:
            await player_search(ctx, player_guid, guid=True, silent=silent)


@bot.command(name=commands.ASK_COMMAND,
             help=commands.ASK_DESCRIPTION,
             aliases=commands.ASK_ALIASES)
@log_command
async def ask_chatgpt(ctx, *params):
    """ Ask OpenAI ChatGPT a question """
    # TODO: Allow each file to invoke it's own logger with the correct context
    logger = get_logger_with_context(ctx)

    prompt = " ".join(params)

    try:
        resp = await openai.ask_chatgpt(prompt, logger)
    except Exception as exc:
        logger.warning(exc, exc_info=_should_log_traceback(exc))

    await ctx.send(resp)


def _should_log_traceback(exc):
    """ Returns True if a traceback should be logged,
    otherwise False
    """
    # TODO: Change to subclass and check instance variable flag
    return exc.__class__.__name__ not in (
        "NoSeasonDataError"
        "UserDoesNotExist",
        "UserStatisticsNotFound",
    )


# Make a partial app.run to pass args/kwargs to it
partial_run = partial(app.run, host="127.0.0.1", port=5000, debug=True, use_reloader=False)
t = Thread(target=partial_run)
t.start()

# Run the bot
bot.run(DISCORD_BOT_TOKEN)
