from collections import defaultdict

import utils.discord as discord_utils
from database.mysql import MySQL


async def send_stats_diff_today(ctx, username):
    """ Sends the stats diff between today and the last play date """
    mysql = await MySQL.create()
    season_id = discord_utils.get_season_id()

    player_snapshots = await mysql.fetch_player_stats_diff_today(
        username,
        season_id)

    stats_breakdown = _breakdown_player_snapshots(player_snapshots)

    message = _create_stats_diff_message(username, stats_breakdown)
    await ctx.send(embed=message)


def _breakdown_player_snapshots(player_snapshots):
    """ Format player snapshots into a dict with current and diff data """
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


def _create_stats_diff_message(username, stats_breakdown):
    """ Create opponent stats Discord message """
    return discord_utils.create_stats_message(
        title=f"Username: {username}",
        desc=_create_wins_diff_str(stats_breakdown["all"]),
        color_metric=stats_breakdown["all"]["KD"]["current"],
        create_stats_func=_create_stats_diff_str,
        stats_breakdown=stats_breakdown,
        username=username
    )


def _create_wins_diff_str(win_stats):
    """ Create stats string for output """
    wins_str = f"{int(win_stats['Top1']['current'])} ({win_stats['Top1']['diff']})"
    matches_str = f"{int(win_stats['Matches']['current']):,} ({win_stats['Matches']['diff']}) played"
    return f"Wins: {wins_str} / {matches_str}"


def _create_stats_diff_str(mode, stats_breakdown):
    """ Create stats string for output """
    mode_stats = stats_breakdown[mode]
    return (f"KD: {mode_stats['KD']['current']} ({mode_stats['KD']['diff']}) • "
            f"Wins: {int(mode_stats['Top1']['current'])} ({mode_stats['Top1']['diff']}) • "
            f"Win Percentage: {mode_stats['WinRatio']['current']:,.1f}% ({mode_stats['WinRatio']['diff']}%) • "
            f"Matches: {int(mode_stats['Matches']['current'])} ({mode_stats['Matches']['diff']}) • "
            f"TRN: {int(mode_stats['TRNRating']['current'])} ({mode_stats['TRNRating']['diff']})")


async def send_opponent_stats_today(ctx):
    """ Outputs the stats of the opponents faced today """
    mysql = await MySQL.create()
    opponent_avg_stats = await mysql.fetch_avg_player_stats_today()

    if not opponent_avg_stats:
        await ctx.send("No opponents played today yet. Get some games in!")
        return

    opponent_stats_breakdown = _breakdown_opponent_average_stats(opponent_avg_stats)

    message = _create_opponents_stats_message(opponent_stats_breakdown)
    await ctx.send(embed=message)


def _breakdown_opponent_average_stats(opponent_avg_stats):
    """ Format opponent avg stats into a dict """
    stats = {}

    # Format data
    for row in opponent_avg_stats:
        mode = row["MODE"]

        stats[mode] = {
            "KD": row["AVG(kd)"],
            "Top1": row["AVG(wins)"],
            "WinRatio": row["AVG(win_rate)"],
            "Matches": row["AVG(games)"],
            "TRNRating": row["AVG(trn)"]
        }

    return stats


def _create_opponents_stats_message(opponent_stats_breakdown):
    """ Create opponent stats Discord message """
    return discord_utils.create_stats_message(
        title="Opponent Average Stats Today",
        desc=discord_utils.create_wins_str(opponent_stats_breakdown["all"]),
        color_metric=opponent_stats_breakdown["all"]["KD"],
        create_stats_func=_create_opponent_stats_str,
        stats_breakdown=opponent_stats_breakdown
    )


def _create_opponent_stats_str(mode, opponent_stats_breakdown):
    """ Create stats string for output """
    mode_stats = opponent_stats_breakdown[mode]
    return (f"KD: {mode_stats['KD']:,.2f} • "
            f"Wins: {int(mode_stats['Top1'])} • "
            f"Win Percentage: {mode_stats['WinRatio']:,.1f}% • "
            f"Matches: {int(mode_stats['Matches'])} • "
            f"TRN: {int(mode_stats['TRNRating'])} ")


async def rate_opponent_stats_today(ctx):
    """ Send the skill rate keyword indicator for the average opponent faced today """
    mysql = await MySQL.create()
    opponent_stats = await mysql.fetch_avg_player_stats_today()

    opponent_stats_breakdown = _breakdown_opponent_average_stats(opponent_stats)

    skill_rate = discord_utils.calculate_skill_rate_indicator(
        opponent_stats_breakdown["all"]["KD"])
    await ctx.send(skill_rate)
