import os
from collections import defaultdict
from urllib.parse import quote

import discord

from database.mysql import MySQL


"""
WIP: See TODO below. File needs to be refactored.
"""


async def get_stats_diff_today(ctx, username):
    """ TODO: "output" instead """
    mysql = await MySQL.create()
    player_snapshots = await mysql.fetch_player_stats_diff_today(
        username,
        _get_season_id())

    stats_breakdown = _breakdown_player_snapshots(player_snapshots)

    message = _create_message(username, stats_breakdown)
    await ctx.send(embed=message)


def _breakdown_player_snapshots(player_snapshots):
    """ Format player snapshots into a dict
    TODO: This function is WIP and temporary until the TODO below is fixed
    TODO: Store just the diff
    """
    processed_snapshots = {
        "previous": {},
        "current": {}
    }
    available_modes = set()

    # Preprocess rows
    for row in player_snapshots:
        mode = row["mode"]
        available_modes.add(mode)
        recency_key = "current" if row["date_rank"] == 1 else "previous"
        processed_snapshots[recency_key][mode] = row

    # Format data
    stats = {}
    for mode in available_modes:
        row_current = processed_snapshots["current"][mode]
        row_previous = processed_snapshots["previous"].get(mode, defaultdict(int))

        stats[mode] = {
            "KD": {
                "current": row_current.get("kd", 0),
                "diff": _pad_symbol(f'{row_current.get("kd", 0) - row_previous.get("kd", 0):,.2f}')
            },
            "Top1": {
                "current": row_current.get("wins", 0),
                "diff": _pad_symbol(f'{row_current.get("wins", 0) - row_previous.get("wins", 0):,}')
            },
            "WinRatio": {
                "current": row_current.get("win_rate", 0),
                "diff": _pad_symbol(f'{row_current.get("win_rate", 0) - row_previous.get("win_rate", 0):,.1f}')
            },
            "Matches": {
                "current": row_current.get("games", 0),
                "diff": _pad_symbol(f'{row_current.get("games", 0) - row_previous.get("games", 0):,}')
            },
            "TRNRating": {
                "current": row_current.get("trn", 0),
                "diff": _pad_symbol(f'{row_current.get("trn", 0) - row_previous.get("trn", 0)}')
            }
        }

    return stats

def _pad_symbol(val: str):
    """ Left pad a plus sign if the number if above zero """
    return f"+{val}" if float(val) >= 0 else val

def _breakdown_opponent_average_stats(opponent_stats):
    """ Format opponent snapshots into a dict
    TODO: Refactor as part of discord_base
    """

    stats = {}
    # Format data
    for row in opponent_stats:
        mode = row["MODE"]

        stats[mode] = {
            "KD": row["AVG(kd)"],
            "Wins": row["AVG(wins)"],
            "Win Percentage": row["AVG(win_rate)"],
            "Matches": row["AVG(games)"],
            "TRNRating": row["AVG(trn)"]
        }

    return stats

def _create_opponents_message(opponent_stats_breakdown):
    """ Create Discord message """
    embed=discord.Embed(
        title="Opponent Average Stats Today",
        description=_create_opponent_wins_str(opponent_stats_breakdown['all']),
        color=_calculate_skill_color_indicator(opponent_stats_breakdown["all"]["KD"]))

    for mode in MODES:
        if mode not in opponent_stats_breakdown:
            continue

        if mode == "all":
            name = "Overall"
        else:
            name = mode.capitalize()

        embed.add_field(name=f"[{name}]", value=_create_opponent_stats_str(mode, opponent_stats_breakdown), inline=False)

    return embed

def _create_opponent_wins_str(opponent_win_stats):
    """ Create opponent stats string for output """
    wins_str = int(opponent_win_stats["Wins"])
    matches_str = int(opponent_win_stats["Matches"])
    return f"Wins: {wins_str} / {matches_str} played" 

def _create_opponent_stats_str(mode, opponent_stats_breakdown):
    """ Create stats string for output """
    mode_stats = opponent_stats_breakdown[mode]
    return (f"KD: {mode_stats['KD']:,.2f} • "
            f"Wins: {int(mode_stats['Wins'])} • "
            f"Win Percentage: {mode_stats['Win Percentage']:,.1f}% • "
            f"Matches: {int(mode_stats['Matches'])} • "
            f"TRN: {int(mode_stats['TRNRating'])} ")

async def get_opponent_stats_today(ctx):
    """ Outputs the stats of the opponents faced today """
    mysql = await MySQL.create()
    opponent_stats = await mysql.fetch_avg_player_stats_today()

    opponent_stats_breakdown = _breakdown_opponent_average_stats(opponent_stats)

    message = _create_opponents_message(opponent_stats_breakdown)
    await ctx.send(embed=message)

async def rate_opponent_stats_today(ctx):
    """ Outputs the stats of the opponents faced today """
    mysql = await MySQL.create()
    opponent_stats = await mysql.fetch_avg_player_stats_today()

    opponent_stats_breakdown = _breakdown_opponent_average_stats(opponent_stats)

    message = _calculate_skill_rate_indicator(opponent_stats_breakdown["all"]["KD"])
    await ctx.send(message)


# TODO: Move the following to discord_base so they can be inherited and overloaded
#       Scrappy temporary solution until I have more time
# _create_stats_str as overridden func
ACCOUNT_PROFILE_URL = "https://fortnitetracker.com/profile/all/{username}?season={season}"

MODES = [
    "solo",
    "duos",
    "trios",
    "squads",
    "all"
]

def _get_season_id():
    """ Returns the latest season ID that the bot knows of """
    return int(os.getenv("FORTNITE_SEASON_ID"))


def _create_message(username, stats_breakdown):
    """ Create Discord message """
    embed=discord.Embed(
        title=f"Username: {username}",
        url=ACCOUNT_PROFILE_URL.format(username=quote(username), season=_get_season_id()),
        description=_create_wins_str(stats_breakdown['all']),
        color=_calculate_skill_color_indicator(stats_breakdown["all"]["KD"]["current"]))

    for mode in MODES:
        if mode not in stats_breakdown:
            continue

        if mode == "all":
            name = "Overall"
        else:
            name = mode.capitalize()

        embed.add_field(name=f"[{name}]", value=_create_stats_str(mode, stats_breakdown), inline=False)

    return embed


def _create_wins_str(win_stats):
    """ Create stats string for output """
    wins_str = f"{int(win_stats['Top1']['current'])} ({win_stats['Top1']['diff']})"
    matches_str = f"{int(win_stats['Matches']['current']):,} ({win_stats['Matches']['diff']}) played"
    return f"Wins: {wins_str} / {matches_str}"


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

def _calculate_skill_rate_indicator(overall_kd):
    """ Return the skill rate indicator """
    if overall_kd >= 5:
        return "Hackers"
    elif overall_kd >= 4:
        return "Aim Botters"   
    elif overall_kd >= 3:
        return "Sweats"
    elif overall_kd < 3 and overall_kd >= 2:
        return "High"
    elif overall_kd < 2 and overall_kd >= 1:
        return "Medium"
    else:
        return "Bots"


def _create_stats_str(mode, stats_breakdown):
    """ Create stats string for output """
    mode_stats = stats_breakdown[mode]
    return (f"KD: {mode_stats['KD']['current']} ({mode_stats['KD']['diff']}) • "
            f"Wins: {int(mode_stats['Top1']['current'])} ({mode_stats['Top1']['diff']}) • "
            f"Win Percentage: {mode_stats['WinRatio']['current']:,.1f}% ({mode_stats['WinRatio']['diff']}%) • "
            f"Matches: {int(mode_stats['Matches']['current'])} ({mode_stats['Matches']['diff']}) • "
            f"TRN: {int(mode_stats['TRNRating']['current'])} ({mode_stats['TRNRating']['diff']})")
