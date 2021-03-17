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
    logger = get_logger_with_context("Main")
    logger.info("Started up %s", bot.user.name)
    logger.info("Bot running on servers: %s",
                ", ".join([guild.name for guild in bot.guilds]))


@bot.event
async def on_guild_join(guild):
    """ Event handler to log when the bot joins a new server """
    logger = get_logger_with_context("Main")
    logger.info("Bot added to new server! Server name: %s", guild.name)


@bot.command(name="hunted", help="shows player stats", aliases=["player", "findnoob", "wreckedby"])
async def player_search(ctx, *player_name):
    """ Searches for a player's stats, output to Discord, and log in database """
    player_name = " ".join(player_name)
    server = ctx.guild.name
    author = ctx.author
    identifier = server + ":" + str(author)

    logger = get_logger_with_context(identifier)
    logger.info("Looking up stats for '%s' ", player_name)

    if not player_name:
        await ctx.send("Please specify an Epic username after the command, "
            "ex: `!hunted LigmaBalls12`")
        return

    try:
        await fortnite_tracker.get_player_stats(ctx, player_name)
    except Exception as e:
        logger.warning(e)
        logger.warning(f"Falling back to Fortnite API for '{player_name}'..",
                       exc_info=should_log_traceback(e))
        await fortnite_api.get_player_stats(ctx, player_name)


@bot.command(name="track", help="tracks the current stats of the squad players")
async def track(ctx):
    """ Tracks the current stats of the squad players """
    tasks = [player_search(ctx, username) for username in SQUAD_PLAYERS_LIST]
    await asyncio.gather(*tasks)


@bot.command(name="stats-today", help="returns the stats of the players faced today",
             aliases=["noobs-killed", "stats", "noobs"])
async def player_stats_today(ctx):
    """ Returns the stats of the players faced today """
    # TODO: Wrap this up
    res = await stats.get_player_stats_today()
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


def get_logger_with_context(identifier):
    """ Returns a LoggerAdapter with context """
    extra = {
        "identifier" : identifier
    }
    return logging.LoggerAdapter(logging.getLogger(__name__), extra)

logger = configure_logger()
bot.run(DISCORD_BOT_TOKEN)
