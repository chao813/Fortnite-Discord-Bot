import os

import aiohttp
import discord


FORTNITE_API_TOKEN = os.getenv("FORTNITE_API_TOKEN")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")

FORTNITE_ACCOUNT_ID_URL = "https://fortniteapi.io/lookup?username={username}&platform={platform}"
FORTNITE_PLAYER_STATS_URL = "https://fortniteapi.io/stats?account={accountid}"
FORTNITE_RECENT_MATCHES_URL = "https://fortniteapi.io/matches?account={}"
FORTNITE_TRACKER_URL = "https://fortnitetracker.com/profile/all/{username}"
TWITCH_AUTHENTICATION_URL = "https://id.twitch.tv/oauth2/token?client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials"
TWITCH_STREAM_URL = "https://api.twitch.tv/helix/streams?game_id={game_id}&first=100&user_login={user_login}"
TWITCH_GAME_URL = "https://api.twitch.tv/helix/games?name=Fortnite"


async def get_player_stats(ctx, player_name, guid):
    async with aiohttp.ClientSession() as session:
        account_id = player_name
        if not guid:
            result = await _get_player_account_id(session, player_name, "")

            if not result["result"]:
                await ctx.send("No Epic username found")
                return

            account_id = result["account_id"]

        stats = await _get_player_stats(session, account_id)
        if stats["global_stats"] is None:
            # Try psn/xbl as player's platform
            result = await _get_player_account_id(session, player_name, "psn")
            stats = await _get_player_stats(session, account_id)
            if stats["global_stats"] is None:
                hidden_player_name = stats["name"]
                stats_hidden_embed=discord.Embed(title=f"{hidden_player_name}'s statistics are hidden")
                await ctx.send(embed=stats_hidden_embed)
                return

        username = stats["name"]
        level = stats["account"].get("level", 0)

        solo = stats["global_stats"].get("solo", {})
        duo = stats["global_stats"].get("duo", {})
        squad = stats["global_stats"].get("squad", {})

        solo_stats = _calculate_stats(solo)
        duo_stats = _calculate_stats(duo)
        squad_stats = _calculate_stats(squad)
        overall_stats, ranking_color = _calculate_overall_stats(solo, duo, squad)

        twitch_stream = await _get_twitch_stream(session, username)

        output = _construct_output(username, ranking_color, level, solo_stats, duo_stats, squad_stats, overall_stats, twitch_stream)
        await ctx.send(embed=output)


async def _get_player_account_id(session, player_name, platform):
    """
    Get account id given player name and platform
    """
    raw_response = await session.get(
        FORTNITE_ACCOUNT_ID_URL.format(username=player_name, platform=platform), headers={"Authorization": FORTNITE_API_TOKEN}
    )
    return await raw_response.json()


async def _get_player_stats(session, account_id):
    """
    Get player stats given account id
    """
    raw_response = await session.get(
        FORTNITE_PLAYER_STATS_URL.format(accountid=account_id), headers={"Authorization": FORTNITE_API_TOKEN}
    )
    return await raw_response.json()


def _calculate_stats(game_mode):
    """
    Calculate player stats in specific game mode
    """
    return "KD: {KD}, Wins: {wins}, Win %: {win_percentage:0.2f}%, Kills: {kills}, Matches Played: {matches_played} \n".format(
        KD=game_mode.get("kd", 0), wins=game_mode.get("placetop1", 0), win_percentage=round(game_mode.get("winrate", 0)*100,2),
        kills=game_mode.get("kills", 0), matches_played=game_mode.get("matchesplayed", 0)
    )


def _calculate_overall_stats(solo, duo, squad):
    """
    Calculate player's overall stats using solo, duo, squad stats
    """
    overall_kd = (solo.get("kd", 0) + duo.get("kd", 0) + squad.get("kd", 0))/3
    overall_wins = solo.get("placetop1", 0) + duo.get("placetop1", 0) + squad.get("placetop1", 0)
    overall_winp = ((solo.get("winrate", 0)*100) + (duo.get("winrate", 0)*100) + (squad.get("winrate", 0)*100))/3
    overall_kills = solo.get("kills", 0) + duo.get("kills", 0) + squad.get("kills", 0)
    overall_matchplayed = solo.get("matchesplayed", 0) + duo.get("matchesplayed", 0) + squad.get("matchesplayed", 0)

    if overall_kd >= 3:
        ranking_color = 0xa600ff
    elif overall_kd < 3 and overall_kd >= 2:
        ranking_color = 0xff0000
    elif overall_kd < 2 and overall_kd >= 1:
        ranking_color = 0xff8800
    else:
        ranking_color = 0x17b532

    overall_stats = "KD: {KD:0.2f}, Wins: {wins}, Win %: {win_percentage:0.2f}%, Kills: {kills}, Matches Played: {matches_played} \n".format(
        KD=overall_kd, wins=overall_wins, win_percentage=overall_winp, kills=overall_kills, matches_played=overall_matchplayed
    )
    return overall_stats, ranking_color


async def _get_twitch_stream(session, username):
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
        twitch_stream = "https://www.twitch.tv/{username}".format(username=username)
    return twitch_stream


def _construct_output(username, ranking_color, level, solo_stats, duo_stats, squad_stats, overall_stats, twitch_stream):
    """
    Format output
    """
    embed=discord.Embed(title="Username: " + username,
                    url=FORTNITE_TRACKER_URL.format(username=username.replace(" ", "%20")),
                    description="Level: " + str(level),
                    color=ranking_color)
    embed.add_field(name="[Solo]" , value=solo_stats, inline=False)
    embed.add_field(name="[Duo]", value=duo_stats, inline=False)
    embed.add_field(name="[Squad]", value=squad_stats, inline=False)
    embed.add_field(name= "[Overall]", value=overall_stats, inline=False)
    if twitch_stream != "":
        embed.add_field(name="[Twitch]", value="[Streaming here]({stream_url})".format(stream_url=twitch_stream), inline=False)
    embed.add_field(name= "[Source]", value="Fortnite API", inline=False)
    return embed
