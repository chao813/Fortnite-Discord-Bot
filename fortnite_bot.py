import aiohttp
import json
import logging
import os

from logging.handlers import TimedRotatingFileHandler
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
FORTNITE_API_TOKEN = os.getenv("FORTNITE_API_TOKEN")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
LOGGER_LEVEL = os.getenv("LOGGER_LEVEL")
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH")

FORTNITE_ACCOUNT_ID_URL = "https://fortniteapi.io/lookup?username={username}&platform={platform}"
FORTNITE_PLAYER_STATS_URL = "https://fortniteapi.io/stats?account={accountid}"
FORTNITE_RECENT_MATCHES_URL = "https://fortniteapi.io/matches?account={}"
FORTNITE_TRACKER_URL = "https://fortnitetracker.com/profile/all/{username}"
TWITCH_AUTHENTICATION_URL = "https://id.twitch.tv/oauth2/token?client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials"
TWITCH_STREAM_URL = "https://api.twitch.tv/helix/streams?game_id={game_id}&first=100&user_login={user_login}"
TWITCH_GAME_URL = "https://api.twitch.tv/helix/games?name=Fortnite"

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
        #await ctx.send(
        #    "Please specify an Epic username after the command, "
        #    "ex: `!hunted LigmaBalls12`")
        await ctx.send(
            embed=discord.Embed(color=discord.Color.green(), description="Hold on! Villager Bot is still starting up!"))

        return

    async with aiohttp.ClientSession() as session:
        result = await get_player_account_id(session, player_name, "")

        if not result["result"]:
            await ctx.send("No Epic username found")
            return

        stats = await get_player_stats(session, result["account_id"])
        if stats["global_stats"] is None:
            #Try psn/xbl as player's platform
            result = await get_player_account_id(session, player_name, "psn")
            stats = await get_player_stats(session, result["account_id"])
            if stats["global_stats"] is None:
                await ctx.send("{player_name}'s statistics are hidden".format(player_name=player_name))
                return

        username = stats["name"]
        level = stats["account"].get("level", 0)

        solo = stats["global_stats"].get("solo", {})
        duo = stats["global_stats"].get("duo", {})    
        squad = stats["global_stats"].get("squad", {})

        solo_stats = calculate_stats(solo, "Solo")
        duo_stats = calculate_stats(duo, "Duo")
        squad_stats = calculate_stats(squad, "Squad")
        overall_stats, ranking_emoji = calculate_overall_stats(solo, duo, squad)
        
        twitch_stream = await get_twitch_stream(session, username)
        output = construct_output(username, ranking_emoji, level, solo_stats, duo_stats, squad_stats, overall_stats, twitch_stream)
        await ctx.send(output)


async def get_player_account_id(session, player_name, platform):
    """
    Get account id given player name and platform
    """
    raw_response = await session.get(
        FORTNITE_ACCOUNT_ID_URL.format(username=player_name, platform=platform), headers={"Authorization": FORTNITE_API_TOKEN}
    )
    return await raw_response.json()


async def get_player_stats(session, account_id):
    """
    Get player stats given account id
    """
    raw_response = await session.get(
        FORTNITE_PLAYER_STATS_URL.format(accountid=account_id), headers={"Authorization": FORTNITE_API_TOKEN}
    )
    return await raw_response.json()


def calculate_stats(game_mode, mode):
    """
    Calculate player stats in specific game mode
    """
    return "[{mode}] - KD: {KD}, Wins: {wins}, Win %: {win_percentage:0.2f}%, Kills: {kills}, Matches Played: {matches_played} \n".format(
        mode=mode, KD=game_mode.get("kd", 0), wins=game_mode.get("placetop1", 0), win_percentage=round(game_mode.get("winrate", 0)*100,2), 
        kills=game_mode.get("kills", 0), matches_played=game_mode.get("matchesplayed", 0)
    )


def calculate_overall_stats(solo, duo, squad):
    """
    Calculate player's overall stats using solo, duo, squad stats
    """
    overall_kd = (solo.get("kd", 0) + duo.get("kd", 0) + squad.get("kd", 0))/3
    overall_wins = solo.get("placetop1", 0) + duo.get("placetop1", 0) + squad.get("placetop1", 0)
    overall_winp = ((solo.get("winrate", 0)*100) + (duo.get("winrate", 0)*100) + (squad.get("winrate", 0)*100))/3
    overall_kills = solo.get("kills", 0) + duo.get("kills", 0) + squad.get("kills", 0)
    overall_matchplayed = solo.get("matchesplayed", 0) + duo.get("matchesplayed", 0) + squad.get("matchesplayed", 0)

    if overall_kd >= 3:
        ranking_emoji = ":purple_circle:"
    elif overall_kd < 3 and overall_kd >= 2:
        ranking_emoji = ":red_circle:"
    elif overall_kd < 2 and overall_kd >= 1:
        ranking_emoji = ":orange_circle:" 
    else:
        ranking_emoji = ":green_circle:"
    
    overall_stats = "[Overall] - KD: {KD:0.2f}, Wins: {wins}, Win %: {win_percentage:0.2f}%, Kills: {kills}, Matches Played: {matches_played} \n".format(
        KD=overall_kd, wins=overall_wins, win_percentage=overall_winp, kills=overall_kills, matches_played=overall_matchplayed
    )
    return overall_stats, ranking_emoji


async def get_twitch_stream(session, username):
    """
    Get Twitch stream if player is streaming
    """
    user_login = username
    if "TTV" in username:
        user_login = username.strip("TTV")
    if "ttv" in username:
        user_login = username.strip("ttv")

    twitch_auth_response = await session.post(TWITCH_AUTHENTICATION_URL.format(client_id=TWITCH_CLIENT_ID, client_secret=TWITCH_CLIENT_SECRET))
    twitch_bearer_token = await twitch_auth_response.json()
    
    twitch_game_reponse = await session.get(TWITCH_GAME_URL, headers={"Authorization": "Bearer " + twitch_bearer_token["access_token"], "Client-ID": TWITCH_CLIENT_ID})
    twitch_game = await twitch_game_reponse.json()    

    twitch_stream_response = await session.get(TWITCH_STREAM_URL.format(game_id=twitch_game["data"][0]["id"], user_login=user_login), headers={"Authorization": "Bearer " + twitch_bearer_token["access_token"], "Client-ID": TWITCH_CLIENT_ID}) 
    twitch_fortnite_streams = await twitch_stream_response.json()

    twitch_stream = ""
    if twitch_stream_response.status == 200 and twitch_fortnite_streams["data"]:
        twitch_stream = "{username} is streaming at https://www.twitch.tv/{username}".format(username=username)
    return twitch_stream


def construct_output(username, ranking_emoji, level, solo_stats, duo_stats, squad_stats, overall_stats, twitch_stream):
    """
    Format output 
    """
    return ("Username: {username} {emoji}\nLevel: {level} \n".format(username=username, emoji=ranking_emoji, level=level) + "```" + 
        solo_stats + duo_stats + squad_stats + "\n" + overall_stats + "```" + FORTNITE_TRACKER_URL.format(username=username.replace(" ", "%20")) + "\n" + twitch_stream
    )


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

