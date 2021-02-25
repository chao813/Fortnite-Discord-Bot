import json
import re

import aiohttp
import discord
from bs4 import BeautifulSoup


ACCOUNT_SEARCH_URL = "https://search-api.tracker.network/search/fortnite?advanced=1&q={username}"
ACCOUNT_PROFILE_URL = "https://fortnitetracker.com/profile/all/{username}?season={season}"
STATS_REGEX = "var imp_data = (.[\s\S]*);"

MODES = [
    "all",
    "solo",
    "duos",
    "squads"
]

HEADERS = {
    "origin": "https://fortnitetracker.com/",
    "referer": "https://fortnitetracker.com/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36"
}


async def get_player_stats(ctx, player_name):
    """ Get player stats and output to Discord """
    username = await _search_username(player_name)
    page_html = await _get_player_profile_html(username)

    soup = BeautifulSoup(page_html, features="html.parser")

    # Find data stored in JS script
    stats = _find_stats_dataset(soup)

    season_stats = _find_season_stats(stats["stats"])

    # TODO: Add more stats to be captured
    message = _create_message(username, _get_kd_breakdown(season_stats))
    await ctx.send(embed=message)


async def _search_username(player_name):
    """ Returns the player's username """
    url = ACCOUNT_SEARCH_URL.format(username=player_name)

    async with aiohttp.ClientSession() as client:
        async with client.get(url, headers=HEADERS) as r:
            assert r.status == 200
            r = await r.json()

    if not r:
        raise ValueError("Username not found in FN Tracker")

    return r[0]["name"]


async def _get_player_profile_html(username):
    """ Get the player stats page in HTML """
    url = ACCOUNT_PROFILE_URL.format(username=username, season=_get_latest_season_id())

    async with aiohttp.ClientSession() as client:
        async with client.get(url, headers=HEADERS) as r:
            print(url)
            print("Status: {}".format(r.status))
            assert r.status == 200
            return await r.text()


def _get_latest_season_id():
    """ Find latest season ID
    TODO: Parse dropdown or something
    """
    return 15


def _find_stats_dataset(soup):
    """ Find the stats dataset from within the script's scripts JS """
    pattern = re.compile(STATS_REGEX)
    scripts = soup.find_all("script", type="text/javascript")
    stats = None

    for script in scripts:
        if pattern.match(str(script.string)):
            data = pattern.match(script.string)
            stats = json.loads(data.groups()[0])

    if stats is None:
        raise ValueError("Site changed, bot broke :/")

    return stats


def _find_season_stats(season_stats):
    """ Find season stats for all platforms combined """
    return next(season for season in season_stats if season["season"] == _get_latest_season_id() and season["platform"] is None)


def _get_kd_breakdown(season_stats):
    """ Find KD for all modes (solo, duo, squad) """
    kd_stats = {}
    for mode in MODES:
        mode_stats = season_stats["stats"].get(mode)
        if mode_stats is None:
            continue
        kd_stats[mode] = _find_mode_kd(mode_stats)

    return kd_stats


def _find_mode_kd(mode):
    """ Find KD within the mode """
    kd_item = next(stat for stat in mode if stat["metadata"]["key"] == "KD")
    return kd_item["value"]


def _create_message(username, kd_breakdown):
    """ Create Discord message """
    embed=discord.Embed(
        title=f"Username: {username}",
        url=ACCOUNT_PROFILE_URL.format(username=username, season=_get_latest_season_id()),
        color=_calculate_skill_color_indicator(kd_breakdown["all"]))

    embed.add_field(name= "[Overall]", value=kd_breakdown["all"], inline=False)

    if "solo" in kd_breakdown:
        embed.add_field(name="[Solo]" , value=kd_breakdown["solo"], inline=False)
    if "duos" in kd_breakdown:
        embed.add_field(name="[Duo]", value=kd_breakdown["duos"], inline=False)
    if "squads" in kd_breakdown:
        embed.add_field(name="[Squad]", value=kd_breakdown["squads"], inline=False)

    return embed

def _calculate_skill_color_indicator(overall_kd):
    """ Return the skill color indicator """
    if overall_kd >= 3:
        return 0xa600ff
    elif overall_kd < 3 and overall_kd >= 2:
        return 0xff0000
    elif overall_kd < 2 and overall_kd >= 1:
        return 0xff8800
    else:
        return 0x17b532
