import logging
import os
from logging.handlers import TimedRotatingFileHandler

from discord.ext import commands
from dotenv import load_dotenv

import clients.fortnite_api as fortnite_api
import clients.fortnite_tracker as fortnite_tracker


load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

LOGGER_LEVEL = os.getenv("LOGGER_LEVEL")
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH")


bot = commands.Bot(command_prefix="!")

@bot.event
async def on_ready():
    logger = get_logger_with_context("Main")
    logger.info("Started up %s", bot.user.name)
    logger.info("Bot running on servers: %s",
                ", ".join([guild.name for guild in bot.guilds]))


@bot.event
async def on_guild_join(guild):
    logger = get_logger_with_context("Main")
    logger.info("Bot added to new server! Server name: %s", guild.name)


@bot.command(name="hunted", help="shows player stats", aliases=["player", "findnoob", "wreckedby"])
async def player_search(ctx, *player_name):
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
        fortnite_tracker.get_player_stats()
    except:  # TODO: Custom exception
        fortnite_api.get_player_stats()


def configure_logger():
    """
    Abstract logger setup
    """
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
    extra = {
        "identifier" : identifier
    }
    return logging.LoggerAdapter(logging.getLogger(__name__), extra)

logger = configure_logger()
bot.run(DISCORD_BOT_TOKEN)
