import os
import asyncio
from copy import deepcopy

import aiohttp

import bot.discord_utils as discord_utils
import core.clients.twitch as twitch
from core.config import config
from core.database.mysql import MySQL
from core.exceptions import UserDoesNotExist, UserStatisticsNotFound
from core.logger import get_logger_with_context
from core.utils.dates import get_playing_session_date


FORTNITE_API_TOKEN = os.getenv("FORTNITE_API_TOKEN")

ACCOUNT_ID_ADVANCED_LOOKUP_URL = "https://fortniteapi.io/v2/lookup/advanced"
PLAYER_STATS_BY_SEASON_URL = "https://fortniteapi.io/v1/stats"
RANKED_INFO_LOOKUP_URL = "https://fortniteapi.io/v2/ranked/user"

# Define mappings for the Player Stats and Get Rank APIs.
# Top-level game mode is defined in the FORTNITE_GAME_MODE_FOR_STATS env variable.
# For some bizarre reason, the APIs have a lot of inconsistencies:
# 1. Both APIs use different keys to mean "ranked"
# 2. Reload stats specifically are split by the map and not the overall game mode
# 3. Reload stats specifically are split by ranked vs unranked
# This means that for BR duos there will be one grouping returned. For Reload duos,
# there will be 6 groupings returned: 2 for each of the 3 maps (ranked and unranked).
# Prefix stats_ are for the Player Stats API
# Prefix rank_ are for the Get Rank API
GAME_MODE_FIELDS = {
    "unranked_br": {
        "stats_code_names": [
            "solo",
            "duos",
            "trios",
            "squads"
        ],
        "rank_code_name": "ranked-br"
    },
    "ranked_br": {
        "stats_code_names": [
            "habanerosolo",
            "habaneroduo",
            "habanerotrio",
            "habanerosquad"
        ],
        "rank_code_name": "ranked-br"
    },
    "ranked_reload": {
        "stats_code_names": [
            "habanero_blastberry",
            "habanero_punchberry",
            "habanero_sunflower"
        ],
        "rank_code_name": "ranked_blastberry_build"
    }
}


async def get_player_stats(ctx, player_name, silent):
    """Get player statistics from fortniteapi.io."""
    account_info = await _get_player_account_info(player_name)

    player_stats, player_rank, twitch_stream = await asyncio.gather(
        _get_player_latest_season_stats(account_info),
        _get_player_rank(account_info),
        twitch.get_twitch_stream(player_name)
    )

    if not player_stats:
        await ctx.send(f"Player has no game records for {_get_readable_sub_mode()}")
        return

    message = _create_message(account_info, player_stats, player_rank, twitch_stream)

    tasks = [_track_player(player_name, player_stats, player_rank)]
    if not silent:
        tasks.append(ctx.send(embed=message))

    await asyncio.gather(*tasks)


async def _get_player_account_info(player_name):
    """Get player account ID using advanced lookup. Advanced lookup
    returns a list of players with similar names, ranked in order of
    match confidence.
    """
    params = {
        "username": player_name
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url=ACCOUNT_ID_ADVANCED_LOOKUP_URL,
            params=params,
            headers=_get_headers()
        ) as resp:
            if resp.status == 404:
                raise UserDoesNotExist(f"Player not found: {player_name}")

            # TODO: Move this elsewhere
            logger = get_logger_with_context(identifier=player_name)

            try:
                resp_json = await resp.json()

                logger.info("Closest username matches: %s", resp_json["matches"])

                best_match = resp_json["matches"][0]
                matched_username = best_match["matches"][0]["value"]
                matched_platform = best_match["matches"][0]["platform"].capitalize()
            except Exception as exc:
                logger.error("Invalid response received from the API: %s. Response: %s", repr(exc), resp_json)
                raise UserDoesNotExist("API broken again.. :/")

            if player_name.lower() == matched_username.lower():
                name = matched_username
            else:
                name = f"{player_name} ({matched_platform}: {matched_username})"

            return {
                "account_id": best_match["accountId"],
                "platform_username": matched_username,
                "readable_name": name
            }


async def _get_player_latest_season_stats(account_info):
    """"Get player stats for the latest season that the player has played in.
    The API will retry another time if the season queried with originally is
    not the most recent season that the player has played in.
    """
    season_id = _get_season_id()
    player_stats = await _get_player_season_stats(account_info, season_id)

    latest_season_id = _get_latest_season_id(player_stats)
    if not _is_latest_season(season_id, latest_season_id):
        _set_fortnite_season_id(latest_season_id)
        # TODO: Move this elsewhere
        logger = get_logger_with_context(identifier=account_info["readable_name"])
        logger.info("Found new season ID, setting latest season ID to: %s", latest_season_id)

        player_stats = await _get_player_season_stats(account_info, latest_season_id)

    mode_breakdown = player_stats["global_stats"]
    mode_breakdown = _filter_to_game_mode(mode_breakdown)
    mode_breakdown = _aggregate_mode_stats(mode_breakdown)
    return mode_breakdown


async def _get_player_season_stats(account_info, season_id):
    """Get player stats for the specified season."""
    account_id = account_info["account_id"]
    readable_name = account_info["readable_name"]

    params = {
        "account": account_id,
        "season": season_id,
        "playlistGrouping": "false"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url=PLAYER_STATS_BY_SEASON_URL,
            params=params,
            headers=_get_headers(),
            raise_for_status=True
        ) as resp:
            resp_json = await resp.json()

            if resp_json["result"] is True:
                if not resp_json["global_stats"]:
                    raise UserStatisticsNotFound(f"Player does not have sufficient data: {readable_name}")
                elif "season" not in resp_json["account"]:
                    raise UserStatisticsNotFound(f"Player does not have available seasons data: {readable_name}")

            if resp_json["result"] is False:
                if "name" not in resp_json:
                    raise UserStatisticsNotFound(f"Player statistics not available at the moment: {readable_name}")
                elif resp_json["name"] is None:
                    raise UserStatisticsNotFound(f"Player statistics not found: {readable_name}")
                else:
                    raise UserStatisticsNotFound(f"Player has a private account: {readable_name}")

            return resp_json


def _get_season_id():
    """Returns the latest season ID that was stored."""
    return config["fortnite"]["season_id"]


def _set_fortnite_season_id(season_id):
    """Set the Fortnite season ID to the latest season ID."""
    config["fortnite"]["season_id"] = season_id


def _get_latest_season_id(player_stats):
    """Retrieves the latest season ID from the player stats history."""
    return max(player_stats["accountLevelHistory"], key=lambda x: x["season"])["season"]


def _is_latest_season(season_id, latest_season_id):
    """Returns True if the season ID requested is for the latest season
    that the player has data on.
    """
    return season_id == latest_season_id


def _get_game_mode_for_stats():
    """Returns the game mode set for stats lookup."""
    return config["fortnite"]["game_mode_for_stats"]


def set_game_mode_for_stats(game_mode):
    """Sets the game mode selected for stats lookup."""
    if game_mode not in GAME_MODE_FIELDS:
        raise ValueError(f"Game mode selected {game_mode} is not supported")
    config["fortnite"]["game_mode_for_stats"] = game_mode


def _get_headers():
    """Return the API headers as a dict."""
    return {
        "Authorization": FORTNITE_API_TOKEN
    }


def _filter_to_game_mode(mode_breakdown):
    """Filter to stats only for the relevant game mode."""
    game_mode = _get_game_mode_for_stats()

    if game_mode in ("unranked_br", "ranked_br"):
        # Filter to the exact code names
        filtered_data = {}
        for mode, stats in mode_breakdown.items():
            br_code_names = GAME_MODE_FIELDS[game_mode]["stats_code_names"]
            if any(mode == code_name for code_name in br_code_names):
                filtered_data[mode] = stats
        return filtered_data

    if game_mode == "ranked_reload":
        # Filter to code names in the game mode
        filtered_data = {}
        for mode, stats in mode_breakdown.items():
            reload_code_names = GAME_MODE_FIELDS[game_mode]["stats_code_names"]
            if any(code_name in mode for code_name in reload_code_names):
                filtered_data[mode] = stats
        return filtered_data


def _aggregate_mode_stats(mode_breakdown):
    """Merge all duo and squad mode stats into independent "duos", "trios", and "squads"
    modes with aggregated stats. Additionally, create a new game mode called "all" which
    is an aggregate of all duos, trios, and squads mode stats.
    """
    base_stats = {
        "placetop1": 0,
        "matchesplayed": 0,
        "winrate": 0,
        "kills": 0,
        "kd": 0,
        "score": 0
    }
    aggregated_mode_breakdown = {
        "all": deepcopy(base_stats),
        "solo": deepcopy(base_stats),
        "duos": deepcopy(base_stats),
        "trios": deepcopy(base_stats),
        "squads": deepcopy(base_stats)
    }
    tracked_modes = set()

    for mode, stats in mode_breakdown.items():
        mode_key = None
        if "duo" in mode:
            mode_key = "duos"
        elif "trio" in mode:
            mode_key = "trios"
        elif "squad" in mode:
            mode_key = "squads"
        if mode_key is None:
            continue
        tracked_modes.add(mode_key)

        # Add individual solo/duo/trio/squad mode stats
        aggregated_mode_breakdown[mode_key]["placetop1"] += stats["placetop1"]
        aggregated_mode_breakdown[mode_key]["matchesplayed"] += stats["matchesplayed"]
        aggregated_mode_breakdown[mode_key]["kills"] += stats["kills"]

        # Add stats to "all" game mode
        aggregated_mode_breakdown["all"]["placetop1"] += stats["placetop1"]
        aggregated_mode_breakdown["all"]["matchesplayed"] += stats["matchesplayed"]
        aggregated_mode_breakdown["all"]["kills"] += stats["kills"]

    # Track "all" game mode after aggregation
    tracked_modes.add("all")

    # Calculate winrate and KD stats
    filtered_mode_breakdown = {}
    for mode, stats in aggregated_mode_breakdown.items():
        if mode not in tracked_modes or stats["matchesplayed"] == 0:
            continue

        aggregated_mode_breakdown[mode]["winrate"] = stats["placetop1"] / stats["matchesplayed"] * 100
        aggregated_mode_breakdown[mode]["kd"] = stats["kills"] / (stats["matchesplayed"] - stats["placetop1"])

        filtered_mode_breakdown[mode] = aggregated_mode_breakdown[mode]

    return filtered_mode_breakdown


async def _get_player_rank(account_info):
    """Get player rank, latest season? not sure what how fortniteapi handles"""
    account_id = account_info["account_id"]
    readable_name = account_info["readable_name"]

    params = {
        "account": account_id
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url=RANKED_INFO_LOOKUP_URL,
            params=params,
            headers=_get_headers(),
            raise_for_status=True
        ) as resp:
            resp_json = await resp.json()

            if resp_json["result"] is True:
                for data in resp_json["rankedData"]:

                    game_mode = _get_game_mode_for_stats()
                    ranking_type = GAME_MODE_FIELDS[game_mode]["rank_code_name"]

                    if data["gameId"] == "fortnite" and data["rankingType"] == ranking_type:
                        return {
                            "rank_name": data["currentDivision"]["name"],
                            "rank_progress": int(data["promotionProgress"] * 100)
                        }
            else:
                raise UserStatisticsNotFound(f"Player rank information not found: {readable_name}")

            return None


def _create_message(account_info, stats_breakdown, player_rank, twitch_stream):
    """ Create player stats Discord message """
    wins_count = stats_breakdown["all"]["placetop1"]
    matches_played = stats_breakdown["all"]["matchesplayed"]
    kd_ratio = stats_breakdown["all"]["kd"]

    return discord_utils.create_stats_message(
        title=f"Username: {account_info['readable_name']}",
        desc=discord_utils.create_wins_str(wins_count, matches_played),
        color_metric=kd_ratio,
        create_stats_func=_create_stats_str,
        stats_breakdown=stats_breakdown,
        username=account_info["platform_username"],
        twitch_stream=twitch_stream,
        rank_name=player_rank.get("rank_name"),
        rank_progress=player_rank.get("rank_progress")
    )


def _create_stats_str(mode, stats_breakdown):
    """ Create stats string for output """
    mode_stats = stats_breakdown[mode]
    return (f"KD: {mode_stats['kd']:.2f} • "
            f"Wins: {int(mode_stats['placetop1']):,} • "
            f"Win Percentage: {mode_stats['winrate']:,.1f}% • "
            f"Matches: {int(mode_stats['matchesplayed']):,}")


async def _track_player(username, stats_breakdown, player_rank):
    """ Insert player stats into database """
    params = []
    for mode, stats in stats_breakdown.items():
        params.append({
            "username": username,
            "season": _get_season_id(),
            "mode": mode,
            "sub_mode": _get_readable_sub_mode(),
            "kd": stats["kd"],
            "games": stats["matchesplayed"],
            "wins": stats["placetop1"],
            "win_rate": stats["winrate"],
            "trn": stats["score"],
            "rank_name": player_rank["rank_name"],
            "rank_progress": player_rank["rank_progress"],
            "date_added": get_playing_session_date()
        })

    mysql = await MySQL.create()
    await mysql.insert_player(params)


def _get_readable_sub_mode():
    """ Get the readable sub mode string, where sub mode is equivalent
    to game mode. Sub mode is used here as `mode` is already used
    downstream including in the database to differentiate between solo,
    duos, trios, squads, and all (aggregated) stats.
    """
    game_mode = _get_game_mode_for_stats()
    return game_mode.replace("_", " ")
