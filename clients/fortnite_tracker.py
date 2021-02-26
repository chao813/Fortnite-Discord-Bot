import json
import re
from collections import defaultdict

import aiohttp
import discord
from bs4 import BeautifulSoup


ACCOUNT_SEARCH_URL = "https://search-api.tracker.network/search/fortnite?advanced=1&q={username}"
ACCOUNT_PROFILE_URL = "https://fortnitetracker.com/profile/all/{username}?season={season}"
STATS_REGEX = "var imp_data = (.[\s\S]*);"
LATEST_SEASON_ID = 15

MODES = [
    "all",
    "solo",
    "duos",
    "squads"
]

STATS = [
    "KD",
    "Top1",
    "WinRatio",
    "Matches",
    "TRNRating"
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
    dataset = _find_stats_dataset(soup)

    # TODO: If latest season has no data, pull lifetime instead of continue searching from past seasons
    season_stats = _find_season_stats(dataset["stats"])

    # Above TODO (quick fix): fail if not enough data found for this season
    if _find_mode_stat("Matches", season_stats["all"]) < 5:
        raise ValueError("Not enough data, reverting to Fortnite API temporarily")

    message = _create_message(username, _get_stats_breakdown(season_stats))
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
            assert r.status == 200
            return await r.text()


def _get_latest_season_id():
    """ Find latest season ID
    TODO: Loop through availableSegments to find the latest season ID. If there
          is a newer season, refetch player profile HTML with the new season ID
    """
    return LATEST_SEASON_ID


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
    return next(stats["stats"] for stats in season_stats if stats["season"] == _get_latest_season_id() and stats["platform"] is None)


def _get_stats_breakdown(season_stats):
    """ Find KD for all modes (solo, duo, squad) """
    breakdown = defaultdict(dict)
    for mode in MODES:
        mode_stats = season_stats.get(mode)
        if mode_stats is None:
            continue
        for stat in STATS:
            breakdown[mode][stat] = _find_mode_stat(stat, mode_stats)

    return breakdown


def _find_mode_stat(stat_name, mode_stats):
    """ Find stats within the game mode """
    stat = next((stat for stat in mode_stats if stat["metadata"]["key"] == stat_name), 0)
    return stat["value"]


def _create_message(username, stats_breakdown):
    """ Create Discord message """
    embed=discord.Embed(
        title=f"Username: {username}",
        url=ACCOUNT_PROFILE_URL.format(username=username, season=_get_latest_season_id()),
        description=f"Wins: {stats_breakdown['all']['Top1']} ({stats_breakdown['all']['Matches']})",
        color=_calculate_skill_color_indicator(stats_breakdown["all"]["KD"]))

    for mode in MODES:
        if mode not in stats_breakdown:
            continue

        if mode == "all":
            name = "Overall"
        else:
            name = mode.capitalize()

        embed.add_field(name=f"[{name}]", value=_create_stats_str(mode, stats_breakdown), inline=False)

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


def _create_stats_str(mode, stats_breakdown):
    """ Create stats string for output """
    mode_stats = stats_breakdown[mode]
    return (f"KD: {mode_stats['KD']} • "
            f"Wins: {int(mode_stats['Top1']):,} • "
            f"Win Percentage: {mode_stats['WinRatio']:,.1f}% • "
            f"Matches: {int(mode_stats['Matches']):,} • "
            f"TRN: {int(mode_stats['TRNRating']):,}")
