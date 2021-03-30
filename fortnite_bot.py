from dotenv import load_dotenv
load_dotenv()


import asyncio
import logging
import os
from logging.handlers import TimedRotatingFileHandler

import discord
from discord.ext.commands import Bot

import commands
import clients.fortnite_api as fortnite_api
import clients.fortnite_tracker as fortnite_tracker
import clients.stats as stats
import clients.interactions as interactions


DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
FORTNITE_DISCORD_ROLE = os.getenv("FORTNITE_DISCORD_ROLE")
FORTNITE_DISCORD_VOICE_CHANNEL_NAME = os.getenv("FORTNITE_DISCORD_VOICE_CHANNEL_NAME")

LOGGER_LEVEL = os.getenv("LOGGER_LEVEL")
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH")

SQUAD_PLAYERS_LIST = os.getenv("SQUAD_PLAYERS_LIST").split(",")

bot = Bot(command_prefix="!")


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


@bot.event
async def on_voice_state_update(member, before, after):
    """ Event handler to track squad stats on voice channel join """
    if not in_fortnite_role(member) or \
       not has_joined_fortnite_voice_channel(before, after) or \
       not is_first_joiner_of_channel(after):
        return

    ctx, silent = await interactions.send_track_question_and_wait(
        bot,
        member.display_name)

    await track(ctx, silent)

def in_fortnite_role(member):
    """ Return True if the member is part of the "fortnite"
    Discord role, otherwise False
    """
    return any(x.name == FORTNITE_DISCORD_ROLE for x in member.roles)


def has_joined_fortnite_voice_channel(before_voice_state, after_voice_state):
    """ Return True if the channel joined is the Fortnite
    voice chat
    """
    channel_before = before_voice_state.channel.name if before_voice_state.channel else None
    channel_after = after_voice_state.channel.name if after_voice_state.channel else None

    switched_channel = channel_before != channel_after
    joined_fortnite_channel = channel_after == FORTNITE_DISCORD_VOICE_CHANNEL_NAME

    return switched_channel and joined_fortnite_channel


def is_first_joiner_of_channel(voice_state):
    """ Return True if the member is the only person in the
    voice channel, otherwise False
    """
    return len(voice_state.channel.members) == 1


@bot.command(name=commands.HELP_COMMAND, help=commands.HELP_DESCRIPTION,
             aliases=commands.HELP_ALIASES)
async def help(ctx):
    """ Lists available commands """
    interactions.send_commands_list(ctx)


@bot.command(name=commands.PLAYER_SEARCH_COMMAND, help=commands.PLAYER_SEARCH_DESCRIPTION,
             aliases=commands.PLAYER_SEARCH_ALIASES)
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
        if silent:
            return

        logger.warning(f"Falling back to Fortnite API for '{player_name}'..")
        await fortnite_api.get_player_stats(ctx, player_name)


@bot.command(name=commands.TRACK_COMMAND, help=commands.TRACK_DESCRIPTION,
             aliases=commands.TRACK_ALIASES)
async def track(ctx, silent=False):
    """ Tracks and logs the current stats of the squad players """
    tasks = [player_search(ctx, username, silent=silent) for username in SQUAD_PLAYERS_LIST]
    await asyncio.gather(*tasks)

@bot.command(name=commands.RATE_COMMAND, help=commands.RATE_DESCRIPTION,
             aliases=commands.RATE_ALIASES)
async def rate(ctx, silent=False):
    """ Rate how good opponents are today """
    await stats.rate_opponent_stats_today(ctx)

@bot.command(name=commands.UPGRADE_COMMAND, help=commands.UPGRADE_DESCRIPTION,
             aliases=commands.UPGRADE_ALIASES)
async def upgrade(ctx, silent=False):
    """ Show map of upgrade locations """
    await ctx.send("https://img.fortniteintel.com/wp-content/uploads/2021/03/17151906/Fortnite-Season-6-upgrade-locations.jpg.webp")

@bot.command(name=commands.HIRE_COMMAND, help=commands.HIRE_DESCRIPTION)
async def hire(ctx, silent=False):
    """ Show map of hireable NPC locations """
    await ctx.send("https://img.fortniteintel.com/wp-content/uploads/2021/03/29172627/Fortnite-hire-NPCs-768x748.jpg.webp")

@bot.command(name=commands.CHESTS_COMMAND, help=commands.CHESTS_DESCRIPTION,
             aliases=commands.CHESTS_ALIASES)
async def chests(ctx, silent=False):
    """ Show map of bunker and regular chest locations """
    chest_location_details = ("1 - Inside a tower that’s located toward the northwest corner of the main structure. \n"
    "2 - Buried in a field to the south of Stealthy Stronghold on a small hill, outside of the walls. \n" 
    "3 - In the house with a red roof under the staircase toward the western part of the town. \n"
    "4 - In the attic of a house toward the landmark’s west. \n"
    "5 - In the building that’s half covered in sand, and the Bunker chest will be waiting for you in its basement. \n"
    "6 - Southeast of the landmark in the sand. \n"
    "7 - In a small campsite west of the Green Steel Bridge. \n"
    "8 - Head over to the house with storm shelter toward the southeastern corner of the landmark. \n"
    "9 - In the attic of a house, located toward the southeastern part of the town. \n"
    "10 - In a field, east of Flopper Pond. \n"
    "11 - In the shack that’s on the top. \n"
    "12 - Near a road that’s west of Durr Burger. \n"
    "13 - Next to the control panel in a house toward the northern edge of the landmark. \n"
    "14 - In a house on the southwestern edge of the landmark. \n"
    "15 - In the flowery fields toward Retail Row’s west. \n"
    "16 - In a field in between Loot Lake and Lazy Lake. \n"
    "17 - Inside of the attic. \n"
    "18 - In the basement of the house and you’ll need to destroy the floor beneath the table with your harvesting tool to access the room. \n"
    "19 - In the large house in the flower fields, located toward the southwest of Misty Meadows. \n"
    "20 - In a shack. \n"
    "21 - In the crossroads between Sweaty Sand and Holly Hedges. \n"
    "22 - Under the sand along the shore line. \n") 
    await ctx.send("https://cdn1.dotesports.com/wp-content/uploads/2021/03/25194519/fortnite-bunker-loc-1024x864.png")
    await ctx.send("```" + chest_location_details + "```")

@bot.command(name=commands.STATS_COMMAND, help="returns the stats based on parameters provided")
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

    if command in commands.STATS_DIFF_COMMANDS:
        logger.info(f"Querying stats diff today for {', '.join(usernames)}")
        await stats_diff_today(ctx, usernames)
    elif command in commands.STATS_OPPONENTS_COMMANDS:
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
    # TODO: 
    await stats.get_opponent_stats_today(ctx)

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
