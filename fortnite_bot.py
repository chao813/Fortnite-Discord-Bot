import aiohttp
import json
import logging
import os
import requests

from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
FORTNITE_API_TOKEN = os.getenv("FORTNITE_API_TOKEN")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")

FORTNITE_ACCOUNT_ID_URL = "https://fortniteapi.io/lookup?username={}"
FORTNITE_PLAYER_STATS_URL = "https://fortniteapi.io/stats?account={}"
FORTNITE_RECENT_MATCHES_URL = "https://fortniteapi.io/matches?account={}"
FORTNITE_TRACKER_URL = "https://fortnitetracker.com/profile/all/{}"
TWITCH_AUTHENTICATION_URL = "https://id.twitch.tv/oauth2/token?client_id={}&client_secret={}&grant_type=client_credentials"
TWITCH_STREAM_URL = "https://api.twitch.tv/helix/streams?game_id={}&first=100&user_login={}"
TWITCH_GAME_URL = "https://api.twitch.tv/helix/games?name=Fortnite"

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

@bot.command(name="hunted", help="shows player stats", aliases=['player', 'findnoob', 'wreckedby'])
async def player_search(ctx, *player_name):
    player_name = " ".join(player_name)
    if not player_name:
        await ctx.send(
            "Please specify an Epic username after the command, "
            "ex: `!hunted LigmaBalls12`")
        return

    async with aiohttp.ClientSession() as session:
        raw_response = await session.get(
            FORTNITE_ACCOUNT_ID_URL.format(player_name), headers={"Authorization": FORTNITE_API_TOKEN})
        result = await raw_response.json()

        if result['result'] == False:
            await ctx.send("No Epic username found")
            return
        if result['result'] == True:
            #GET Global player stats 
            raw_response = await session.get(
            FORTNITE_PLAYER_STATS_URL.format(result['account_id']), headers={"Authorization": FORTNITE_API_TOKEN})
            stats = await raw_response.json()

            username = stats['name']
            solos = stats["global_stats"]["solo"]
            duos = stats["global_stats"]["duo"]
            squads = stats["global_stats"]["squad"]

            solo_stats = "[Solo] - KD: {}, Wins: {}, Win %: {:0.2f}, Kills: {}, Matches Played: {} \n".format(solos["kd"], solos["placetop1"], solos["winrate"]*100, solos["kills"],solos["matchesplayed"])
            duo_stats = "[Duo] - KD: {}, Wins: {}, Win %: {:0.2f}, Kills: {}, Matches Played: {} \n".format(duos["kd"], duos["placetop1"], duos["winrate"]*100, duos["kills"],duos["matchesplayed"])
            squad_stats = "[Squad] - KD: {}, Wins: {}, Win %: {:0.2f}, Kills: {}, Matches Played: {} \n".format(squads["kd"], squads["placetop1"], squads["winrate"]*100, squads["kills"],squads["matchesplayed"])
            
            overall_KD = (solos["kd"] + duos["kd"] + squads["kd"])/3
            overall_wins = solos["placetop1"] + duos["placetop1"] + squads["placetop1"]
            overall_winp = (solos["winrate"] + duos["winrate"] + squads["winrate"])/3
            overall_kills = solos["kills"] + duos["kills"] + squads["kills"]
            overall_matchplayed = solos["matchesplayed"] + duos["matchesplayed"] + squads["matchesplayed"]
            overall_stats = "[Overall] - KD: {:0.2f}, Wins: {}, Win %: {:0.2f}, Kills: {}, Matches Played: {} \n".format(overall_KD, overall_wins, overall_winp*100, overall_kills, overall_matchplayed)

            #GET Recent matches
            # r_response = await session.get(
            # FORTNITE_RECENT_MATCHES_URL.format(result['account_id']), headers={"Authorization": FORTNITE_API_TOKEN})
            # match_stats = await r_response.json()
            
            # for match in match_stats['matches']:
            #     if match_stats['matches']["readable_name"] == "Squads" or match_stats['matches']["readable_name"] == "Solo" or match_stats['matches']["readable_name"] == "Duos"

            
            #Format stats to make it look prettier
            output_stats = "Username: {} \nLevel: {} \n\n".format(stats['name'], stats['account']['level']) + solo_stats + duo_stats + squad_stats + "\n" + overall_stats + FORTNITE_TRACKER_URL.format(stats['name'])
            await ctx.send(output_stats)

            
            #Check to see if player streaming on Twitch
            #if "TTV" in username or "ttv" in username:
            if "TTV" in username:
                user_login = username.strip('TTV')
            elif "ttv" in username:
                user_login = username.strip('ttv')
            else:
                user_login = username

            twitch_auth_response = await session.post(TWITCH_AUTHENTICATION_URL.format(TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET))
            twitch_bearer_token = await twitch_auth_response.json()
            
            twitch_game_reponse = await session.get(TWITCH_GAME_URL, headers={"Authorization": "Bearer " + twitch_bearer_token['access_token'], "Client-ID": TWITCH_CLIENT_ID})
            twitch_game = await twitch_game_reponse.json()

            twitch_stream_response = await session.get(TWITCH_STREAM_URL.format(twitch_game['data'][0]['id'], user_login), headers={"Authorization": "Bearer " + twitch_bearer_token['access_token'], "Client-ID": TWITCH_CLIENT_ID})
            twitch_fortnite_streams = await twitch_stream_response.json()

            if len(twitch_fortnite_streams['data']) != 0:
                await ctx.send("{} is streaming at https://www.twitch.tv/{}".format(username,username))
                            

            


bot.run(DISCORD_BOT_TOKEN)

