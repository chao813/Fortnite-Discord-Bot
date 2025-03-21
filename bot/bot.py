import asyncio
import logging

import discord
from discord.ext.commands import Bot, max_concurrency, BucketType, CommandNotFound

import bot.commands as commands
import bot.interactions as interactions
import bot.stats as stats
import core.clients.fortnite_api as fortnite_api
import core.clients.openai as openai
from core.config import config
from core.exceptions import NoSeasonDataError, UserDoesNotExist, UserStatisticsNotFound
from core.logger import get_logger_with_context, log_command


ACTIVE_PLAYERS_LIST = []
SQUAD_PLAYERS_LIST = config["fortnite"]["players"]
FORTNITE_DISCORD_USERS_DICT = config["discord"]["user_to_fortnite_player"]
FORTNITE_TEXT_CHANNEL_ID = config["discord"]["text_channel_id"]

logger = logging.getLogger(__name__)

bot = Bot(command_prefix="!", intents=discord.Intents.default())

openai.initialize()


@bot.event
async def on_ready():
    """ Event handler to setup logger on load """
    logger = get_logger_with_context(identifier="Main")
    logger.info("Started up %s", bot.user.name)
    logger.info("Bot running on servers: %s",
                ", ".join([guild.name for guild in bot.guilds]))


@bot.event
async def on_command_error(ctx, error):
    """ Event handler to log invalid commands """
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
            if member.display_name in FORTNITE_DISCORD_USERS_DICT:
                if FORTNITE_DISCORD_USERS_DICT[member.display_name] not in ACTIVE_PLAYERS_LIST:
                    ACTIVE_PLAYERS_LIST.append(FORTNITE_DISCORD_USERS_DICT[member.display_name])

        if interactions.should_remove_player_from_squad_player_session_list(member, before, after):
            if member.display_name in FORTNITE_DISCORD_USERS_DICT:
                if FORTNITE_DISCORD_USERS_DICT[member.display_name] in ACTIVE_PLAYERS_LIST:
                    ACTIVE_PLAYERS_LIST.remove(FORTNITE_DISCORD_USERS_DICT[member.display_name])

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


@bot.command(name=commands.MESSAGE_COMMAND,
             help=commands.MESSAGE_DESCRIPTION,
             aliases=commands.MESSAGE_ALIASES)
@log_command
async def send_message(_, *message):
    """ Send message to Discord text channel
    This command is used by external callers such as the Flask service.
    """
    msg = " ".join(message)
    await bot.get_channel(FORTNITE_TEXT_CHANNEL_ID).send(msg)


@bot.command(name=commands.STATS_GAME_MODE_COMMAND,
             help=commands.STATS_GAME_MODE_DESCRIPTION,
             aliases=commands.STATS_GAME_MODE_ALIASES)
@log_command
async def update_game_mode_for_stats(ctx, *game_mode):
    """ Updates the game mode selected for stats lookup """
    game_mode = " ".join(game_mode).lower().replace(" ", "_")

    logger = get_logger_with_context(ctx)
    logger.info("Updating game mode to: %s", game_mode)

    try:
        fortnite_api.set_game_mode_for_stats(game_mode)
    except ValueError as exc:
        logger.warning(exc)
        await ctx.send(exc)
        return

    msg = f"Game mode set: {fortnite_api.get_readable_game_mode(game_mode)}"
    logger.info(msg)
    await ctx.send(msg)


@bot.command(name=commands.PLAYER_SEARCH_COMMAND,
             help=commands.PLAYER_SEARCH_DESCRIPTION,
             aliases=commands.PLAYER_SEARCH_ALIASES)
@max_concurrency(4, per=BucketType.guild, wait=True)
@log_command
async def player_search(ctx, *player_name, game_mode=None, players_killed_desc=None, is_guid=False, silent=False):
    """ Searches for a player's stats, output to Discord, and log in database """
    player_name = " ".join(player_name)

    logger = get_logger_with_context(ctx)
    logger.info("Searching for player stats: %s", player_name)

    if not player_name:
        await ctx.send("Please specify an Epic username after the command, "
                       "ex: `!hunted LigmaBalls12`")
        return

    try:
        await fortnite_api.get_player_stats(
            ctx,
            player_name,
            game_mode,
            players_killed_desc,
            is_guid,
            silent
        )
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
@max_concurrency(1, per=BucketType.guild, wait=True)
@log_command
async def track(ctx, silent=False):
    """ Tracks and logs the current stats of the current players """
    logger = get_logger_with_context(ctx)
    if not (players_list := ACTIVE_PLAYERS_LIST):
        players_list = SQUAD_PLAYERS_LIST
        logger.info("No players active on Discord, tracking all squad players instead")
    tasks = [player_search(ctx, username, is_guid=False, silent=silent) for username in players_list]
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
        update_tasks.append(player_search(ctx, username, is_guid=False, silent=True))
        calculate_tasks.append(stats.send_stats_diff_today(ctx, username))

    await asyncio.gather(*update_tasks)
    await asyncio.gather(*calculate_tasks)


async def _opponent_stats_today(ctx):
    """ Outputs the stats of the players faced today """
    await stats.send_opponent_stats_today(ctx)


@bot.command(name=commands.ASK_COMMAND,
             help=commands.ASK_DESCRIPTION,
             aliases=commands.ASK_ALIASES)
@log_command
async def ask_chatgpt(ctx, *params):
    """ Ask OpenAI ChatGPT a question """
    # TODO: Instead of an ask command, create a command to fetch stats
    #       for all the opponents faced today from the database and then
    #       have GPT analyze the difficulty and provide commentary.
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
