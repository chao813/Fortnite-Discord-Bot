import os
import asyncio

import aiohttp

import utils.discord as discord_utils
import clients.twitch as twitch
from database.mysql import MySQL
from exceptions import UserDoesNotExist, UserStatisticsNotFound
from utils.dates import get_playing_session_date
from logger import get_logger_with_context


FORTNITE_API_TOKEN = os.getenv("FORTNITE_API_TOKEN")

ACCOUNT_ID_ADVANCED_LOOKUP_URL = "https://fortniteapi.io/v2/lookup/advanced"
PLAYER_STATS_BY_SEASON_URL = "https://fortniteapi.io/v1/stats"
RANKED_INFO_LOOKUP_URL = "https://fortniteapi.io/v2/ranked/user"

async def get_player_stats(ctx, player_name, silent):
    """Get player statistics from fortniteapi.io."""
    account_info = await _get_player_account_info(player_name)

    player_stats = await _get_player_latest_season_stats(account_info)
    player_rank = await _get_player_rank(account_info)

    # TODO: Asyncio with above
    twitch_stream = await twitch.get_twitch_stream(player_name)

    message = _create_message(account_info, player_stats, player_rank, twitch_stream)

    tasks = [_track_player(player_name, player_stats)]
    if not silent:
        tasks.append(ctx.send(embed=message))

    await asyncio.gather(*tasks)


async def _get_player_rank(account_info):
    """Get player rank, latest season? not sure what how fortniteapi handles"""
    player_name = account_info["readable_name"]

    params = {
        "username": player_name,
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
                if not resp_json["rankedData"] and resp_json["gameId"] != "fortnite":
                    raise UserStatisticsNotFound(f"Player does not have ranked data: {account_info['readable_name']}")               
                else:
                    return [_ranked_data for _ranked_data in resp_json["rankedData"] if _ranked_data["rankingType"] == "ranked-br"][0]

            return None 


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

                logger.info("Closest username matches: %s", resp_json['matches'])

                best_match = resp_json["matches"][0]
                matched_username = best_match["matches"][0]["value"]
                matched_platform = best_match["matches"][0]["platform"].capitalize()
            except Exception as exc:
                logger.error("Invalid response received from the API: %s", resp_json)
                logger.error(repr(exc))
                raise UserDoesNotExist("API broke and returned bad data..")

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

    if not _is_latest_season(season_id, player_stats):
        latest_season_id = _get_latest_season_id(player_stats)
        _set_fortnite_season_id(latest_season_id)
        # TODO: Move this elsewhere
        logger = get_logger_with_context(identifier=account_info["readable_name"])
        logger.info("Found new season ID, setting latest season ID to: %s", latest_season_id)

        player_stats = await _get_player_season_stats(account_info, latest_season_id)

    mode_breakdown = player_stats["global_stats"]
    mode_breakdown = _append_all_mode_stats(mode_breakdown)
    mode_breakdown = _rename_game_modes(mode_breakdown)
    return mode_breakdown


async def _get_player_season_stats(account_info, season_id):
    """Get player stats for the specified season."""
    account_id = account_info["account_id"]

    params = {
        "account": account_id,
        "season": season_id
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
                if not resp_json["global_stats"] or "season" not in resp_json["account"]:
                    raise UserStatisticsNotFound(f"Player does not have sufficient data: {account_info['readable_name']}")

            if resp_json["result"] is False:
                if resp_json["name"] is None:
                    raise UserStatisticsNotFound(f"Player statistics not found: {account_info['readable_name']}")
                else:
                    raise UserStatisticsNotFound(f"Player has a private account: {account_info['readable_name']}")

            return resp_json


def _get_season_id():
    """Returns the latest season ID that was stored."""
    return int(os.getenv("FORTNITE_SEASON_ID"))


def _set_fortnite_season_id(season_id):
    """ Set the Fortnite season ID to the latest season ID."""
    os.environ["FORTNITE_SEASON_ID"] = str(season_id)


def _is_latest_season(season_id, player_stats):
    """Returns True if the season ID requested is for the latest season
    that the player has data on.
    """
    return season_id == player_stats["account"]["season"]


def _get_latest_season_id(player_stats):
    """Retrieves the latest season ID from the player stats history."""
    return max(player_stats["accountLevelHistory"], key=lambda x:x["season"])["season"]


def _get_headers():
    """Return the API headers as a dict."""
    return {
        "Authorization": FORTNITE_API_TOKEN
    }


def _append_all_mode_stats(mode_breakdown):
    """Append aggregated stats into the dataset as part of the "all" game mode."""
    all_stats = {
        "placetop1": 0,
        "matchesplayed": 0,
        "winrate": 0,
        "kills": 0,
        "kd": 0,
        "score": 0
    }

    for mode, stats in mode_breakdown.items():
        all_stats["placetop1"] += stats["placetop1"]
        all_stats["matchesplayed"] += stats["matchesplayed"]
        all_stats["kills"] += stats["kills"]
        mode_breakdown[mode]["winrate"] = stats["winrate"] * 100

    all_stats["winrate"] = all_stats["placetop1"] / all_stats["matchesplayed"] * 100
    all_stats["kd"] = all_stats["kills"] / (all_stats["matchesplayed"] - all_stats["placetop1"])

    mode_breakdown["all"] = all_stats

    return mode_breakdown


def _rename_game_modes(mode_breakdown):
    """Rename game modes to synchronize with what Discord utils expects."""
    if "duo" in mode_breakdown:
        mode_breakdown["duos"] = mode_breakdown.pop("duo")
    if "trio" in mode_breakdown:
        mode_breakdown["trios"] = mode_breakdown.pop("trio")
    if "squad" in mode_breakdown:
        mode_breakdown["squads"] = mode_breakdown.pop("squad")
    return mode_breakdown


def _create_message(account_info, stats_breakdown, player_rank, twitch_stream):
    """ Create player stats Discord message """
    wins_count = stats_breakdown["all"]["placetop1"]
    matches_played = stats_breakdown["all"]["matchesplayed"]
    kd_ratio = stats_breakdown["all"]["kd"]
    if player_rank:
        rank_name = player_rank["currentDivision"]["name"]
        rank_progress = round(player_rank["promotionProgress"] * 100)

    return discord_utils.create_stats_message(
        title=f"Username: {account_info['readable_name']}",
        desc=discord_utils.create_wins_str(wins_count, matches_played),
        color_metric=kd_ratio,
        create_stats_func=_create_stats_str,
        stats_breakdown=stats_breakdown,
        username=account_info["platform_username"],
        twitch_stream=twitch_stream,
        rank_name=rank_name,
        rank_progress=rank_progress
    )


def _create_stats_str(mode, stats_breakdown):
    """ Create stats string for output """
    mode_stats = stats_breakdown[mode]
    return (f"KD: {mode_stats['kd']:.2f} • "
            f"Wins: {int(mode_stats['placetop1']):,} • "
            f"Win Percentage: {mode_stats['winrate']:,.1f}% • "
            f"Matches: {int(mode_stats['matchesplayed']):,}")


async def _track_player(username, stats_breakdown):
    """ Insert player stats into database """
    params = []
    for mode, stats in stats_breakdown.items():
        params.append({
            "username": username,
            "season": _get_season_id(),
            "mode": mode,
            "kd": stats["kd"],
            "games": stats["matchesplayed"],
            "wins": stats["placetop1"],
            "win_rate": stats["winrate"],
            "trn": stats["score"],
            "date_added": get_playing_session_date()
        })

    mysql = await MySQL.create()
    await mysql.insert_player(params)
