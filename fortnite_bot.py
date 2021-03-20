from dotenv import load_dotenv
load_dotenv()


import asyncio
import logging
import os
from logging.handlers import TimedRotatingFileHandler

from discord.ext import commands

import clients.fortnite_api as fortnite_api
import clients.fortnite_tracker as fortnite_tracker
import clients.stats as stats


DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

LOGGER_LEVEL = os.getenv("LOGGER_LEVEL")
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH")

SQUAD_PLAYERS_LIST = os.getenv("SQUAD_PLAYERS_LIST").split(",")


bot = commands.Bot(command_prefix="!")

@bot.event
async def on_ready():
    """ Event handler to setup logger on load """
    logger = get_logger_with_context(identifier="Main")
    logger.info("Started up %s", bot.user.name)
    logger.info("Bot running on servers: %s",
                ", ".join([guild.name for guild in bot.guilds]))


@bot.event
async def on_guild_join(guild):
    """ Event handler to log when the bot joins a new server """
    logger = get_logger_with_context(identifier="Main")
    logger.info("Bot added to new server! Server name: %s", guild.name)


@bot.command(name="hunted", help="shows player stats",
             aliases=["h", "player", "findnoob", "wreckedby"])
async def player_search(ctx, *player_name, silent=False):
    """ Searches for a player's stats, output to Discord, and log in database """
    player_name = " ".join(player_name)

    logger = get_logger_with_context(ctx)
    logger.info("Looking up stats for '%s' ", player_name)

    if not player_name:
        await ctx.send("Please specify an Epic username after the command, "
            "ex: `!hunted LigmaBalls12`")
        return

    try:
        await fortnite_tracker.get_player_stats(ctx, player_name, silent)
    except Exception as e:
        logger.warning(e, exc_info=should_log_traceback(e))

        # Fortnite API stats are unnecessary in silent mode
        if not silent:
            return

        logger.warning(f"Falling back to Fortnite API for '{player_name}'..")
        await fortnite_api.get_player_stats(ctx, player_name, silent)


@bot.command(name="track", help="tracks the current stats of the squad players",
             aliases=["squad"])
async def track(ctx):
    """ Tracks and logs the current stats of the squad players """
    tasks = [player_search(ctx, username) for username in SQUAD_PLAYERS_LIST]
    await asyncio.gather(*tasks)


@bot.command(name="stats", help="returns the stats based on parameters provided")
async def stats_operations(ctx, *params):
    """ Outputs stats based on the parameters provided.
    Valid parameters are:
        1. today
            - Stats diff of the squad players today
        2. played, opponents, noobs, enemy
            - Stats of the players faced today
    """
    logger = get_logger_with_context(ctx)
    params = list(params)

    command = params.pop(0) if params else None
    if not command:
        message = "Please specify a command, ex: `!stats diff` or `!stats played`"
        logger.warning(message)
        await ctx.send(message)
        return

    usernames = params or SQUAD_PLAYERS_LIST

    if command in ("today", "diff"):
        logger.info(f"Querying stats diff today for {', '.join(usernames)}")
        await stats_diff_today(ctx, usernames)
    elif command in ("played", "opponents", "noobs", "enemy"):
        logger.info("Querying opponent stats today")
        await opponent_stats_today(ctx)
    else:
        await ctx.send(f"Command provided '{command}' is not valid")


async def stats_diff_today(ctx, usernames):
    """ Outputs the stats diff of the squad players today.
    Perform a silent update of the player stats in the database first
    """
    update_tasks = []
    calculate_tasks = []

    for username in usernames:
        update_tasks.append(player_search(ctx, username, silent=True))
        calculate_tasks.append(stats.get_stats_diff_today(ctx, username))

    await asyncio.gather(*update_tasks)
    await asyncio.gather(*calculate_tasks)


async def opponent_stats_today(ctx):
    """ Outputs the stats of the players faced today """
    # TODO: Wrap this up
    res = await stats.get_opponent_stats_today()
    print(res)


def should_log_traceback(e):
    """ Returns True if a traceback should be logged,
    otherwise False
    """
    # TODO: Change to subclass and check instance variable flag
    return e.__class__.__name__ not in ("UserDoesNotExist", "NoSeasonDataError")


def configure_logger():
    """ Abstract logger setup """
    logging.root.setLevel(LOGGER_LEVEL)

    file_handler = TimedRotatingFileHandler(LOG_FILE_PATH, when="W0", interval=7, backupCount=4)
    stream_handler = logging.StreamHandler()

    formatter = logging.Formatter("[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] [%(identifier)s] %(message)s")
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    logger = logging.getLogger(__name__)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


def get_logger_with_context(ctx=None, identifier=None):
    """ Returns a LoggerAdapter with context """
    if not identifier:
        server = ctx.guild.name
        author = ctx.author
        identifier = server + ":" + str(author)

    extra = {
        "identifier" : identifier
    }
    return logging.LoggerAdapter(logging.getLogger(__name__), extra)


logger = configure_logger()
bot.run(DISCORD_BOT_TOKEN)
