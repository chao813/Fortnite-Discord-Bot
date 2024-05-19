"""
NOTE: 3/5/2023
Fortnite Tracker has been deprecated due to Cloudflare restrictions.
"""

import asyncio
import json
import os
import re
from collections import defaultdict
from urllib.parse import unquote

from bs4 import BeautifulSoup

import utils.discord as discord_utils
from database.mysql import MySQL
from exceptions import UserDoesNotExist, NoSeasonDataError
from utils.cloudscraper import cloudscrape, Method
from utils.dates import get_playing_session_date


ACCOUNT_SEARCH_URL = "https://fortnitetracker.com/profile/search?q={username}"
ACCOUNT_PROFILE_URL = "https://fortnitetracker.com/profile/all/{username}?season={season}"
STATS_PATTERN = "const profile = "
STATS_REGEX = f"\s*{STATS_PATTERN}(.*);"

MODES = [
    "solo",
    "duos",
    "trios",
    "squads",
    "all"
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


async def get_player_stats(ctx, player_name, silent):
    """ Get player stats and output to Discord """
    username = await _search_username(player_name)
    season_stats = await _get_player_season_dataset(username)

    stats_breakdown = _get_stats_breakdown(season_stats)

    message = _create_message(username, stats_breakdown)

    tasks = [_track_player(username, stats_breakdown)]
    if not silent:
        tasks.append(ctx.send(embed=message))

    await asyncio.gather(*tasks)


async def _search_username(player_name):
    """ Returns the player's username """
    url = ACCOUNT_SEARCH_URL.format(username=player_name)

    resp = await cloudscrape(Method.GET, url, headers=HEADERS, allow_redirects=False)
    if resp.status_code == 302:
        return unquote(resp.headers["Location"].split("/")[-1])

    raise UserDoesNotExist(f"Username not found in FN Tracker: {player_name}")


async def _get_player_season_dataset(username):
    """ Get the player's season statistics """
    dataset = await _get_player_dataset(username)

    latest_season_id = _find_latest_season_id(dataset["availableSegments"])

    if _newer_season_available(latest_season_id):
        _set_fortnite_season_id(latest_season_id)
        dataset = await _get_player_dataset(username)

    # TODO: If latest season has no data, pull lifetime instead of continue searching from past seasons
    return _find_season_stats(dataset["stats"], username)


async def _get_player_dataset(username):
    """ Fetch player profile HTML and parse statistics dataset to dict """
    page_html = await _get_player_profile_html(username)
    soup = BeautifulSoup(page_html, features="html.parser")
    return _find_stats_segment(soup)


async def _get_player_profile_html(username):
    """ Get the player stats page in HTML """
    url = ACCOUNT_PROFILE_URL.format(username=username, season=_get_season_id())

    resp = await cloudscrape(Method.GET, url, headers=HEADERS)
    resp.raise_for_status()
    return resp.text


def _find_stats_segment(soup):
    """ Find the stats dataset from within the script's scripts JS """
    re_pattern = re.compile(STATS_REGEX)
    script_tags = soup.find_all("script")
    retrieved_stats = None

    for script in script_tags:
        script_text = script.text

        if STATS_PATTERN not in script_text:
            continue

        re_match = re_pattern.match(script_text)

        if re_match is not None:
            retrieved_stats = json.loads(re_match.groups()[0])
            break

    if retrieved_stats is None:
        raise ValueError("Site changed and stats JSON is no longer there, bot broke :/")

    return retrieved_stats


def _find_latest_season_id(segments):
    """ Returns the latest season ID with available data """
    return max([seg["season"] for seg in segments if seg["season"] is not None])


def _newer_season_available(latest_season_id):
    """ Returns True if there is a newer Fortnite season available,
    otherwise return False
    """
    return latest_season_id > _get_season_id()


def _get_season_id():
    """ Returns the latest season ID that the bot knows of """
    return int(os.getenv("FORTNITE_SEASON_ID"))


def _set_fortnite_season_id(season_id):
    """ Set the Fortnite season ID to the latest season ID """
    os.environ["FORTNITE_SEASON_ID"] = str(season_id)


def _find_season_stats(season_stats, username):
    """ Find season stats for all platforms combined """
    try:
        return next(stats["stats"] for stats in season_stats if
                    _is_latest_season(stats["season"]) and
                    _is_combined_platform(stats["platform"]))
    except StopIteration as e:
        # TODO (quick fix): fail if no data was found for the season
        raise NoSeasonDataError(f"No data found in this season for '{username}'")


def _is_latest_season(season_id):
    """ Return True if the season ID is the latest season,
    otherwise return False
    """
    return season_id == _get_season_id()


def _is_combined_platform(platform):
    """ Return True if the dataset is for all platforms combined,
    otherwise return False
    """
    return platform is None


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
    """ Create player stats Discord message """
    wins_count = stats_breakdown["all"]["Top1"]
    matches_played = stats_breakdown["all"]["Matches"]
    kd_ratio = stats_breakdown["all"]["KD"]

    return discord_utils.create_stats_message(
        title=f"Username: {username}",
        desc=discord_utils.create_wins_str(wins_count, matches_played),
        color_metric=kd_ratio,
        create_stats_func=_create_stats_str,
        stats_breakdown=stats_breakdown,
        username=username,
    )


def _create_stats_str(mode, stats_breakdown):
    """ Create stats string for output """
    mode_stats = stats_breakdown[mode]
    return (f"KD: {mode_stats['KD']} • "
            f"Wins: {int(mode_stats['Top1']):,} • "
            f"Win Percentage: {mode_stats['WinRatio']:,.1f}% • "
            f"Matches: {int(mode_stats['Matches']):,} • "
            f"TRN: {int(mode_stats['TRNRating']):,}")


async def _track_player(username, stats_breakdown):
    """ Insert player stats into database """
    params = []
    for mode, stats in stats_breakdown.items():
        params.append({
            "username": username,
            "season": _get_season_id(),
            "mode": mode,
            "kd": stats["KD"],
            "games": stats["Matches"],
            "wins": stats["Top1"],
            "win_rate": stats["WinRatio"],
            "trn": stats["TRNRating"],
            "date_added": get_playing_session_date()
        })

    mysql = await MySQL.create()
    await mysql.insert_player(params)
