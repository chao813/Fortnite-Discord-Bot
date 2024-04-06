import os
from urllib.parse import quote

import discord


ACCOUNT_PROFILE_URL = "https://fortnitetracker.com/profile/all/{username}?season={season}"

FORTNITE_DISCORD_ROLE = os.getenv("FORTNITE_DISCORD_ROLE")
FORTNITE_DISCORD_VOICE_CHANNEL_NAME = os.getenv("FORTNITE_DISCORD_VOICE_CHANNEL_NAME")

MODES = [
    "solo",
    "duos",
    "trios",
    "squads",
    "all"
]

RANK_ICONS = {
    "unranked": "https://static.wikia.nocookie.net/fortnite/images/0/0d/Unknown_Rank_-_Icon_-_Fortnite.png/revision/latest/scale-to-width-down/100?cb=20230531202915",
    "bronze i": "https://static.wikia.nocookie.net/fortnite/images/4/44/Bronze_I_-_Icon_-_Fortnite.png/revision/latest/scale-to-width-down/100?cb=20230531201220",
    "bronze ii": "https://static.wikia.nocookie.net/fortnite/images/9/92/Bronze_II_-_Icon_-_Fortnite.png/revision/latest/scale-to-width-down/100?cb=20230531201221",
    "bronze iii": "https://static.wikia.nocookie.net/fortnite/images/7/74/Bronze_III_-_Icon_-_Fortnite.png/revision/latest/scale-to-width-down/100?cb=20230531201222",
    "silver i": "https://static.wikia.nocookie.net/fortnite/images/c/c3/Silver_I_-_Icon_-_Fortnite.png/revision/latest/scale-to-width-down/100?cb=20230531201235",
    "silver ii": "https://static.wikia.nocookie.net/fortnite/images/1/1d/Silver_II_-_Icon_-_Fortnite.png/revision/latest/scale-to-width-down/100?cb=20230531201236",
    "silver iii": "https://static.wikia.nocookie.net/fortnite/images/0/0a/Silver_III_-_Icon_-_Fortnite.png/revision/latest/scale-to-width-down/100?cb=20230531201237",
    "gold i": "https://static.wikia.nocookie.net/fortnite/images/3/37/Gold_I_-_Icon_-_Fortnite.png/revision/latest/scale-to-width-down/100?cb=20230531201229",
    "gold ii": "https://static.wikia.nocookie.net/fortnite/images/f/fb/Gold_II_-_Icon_-_Fortnite.png/revision/latest/scale-to-width-down/100?cb=20230531201230",
    "gold iii": "https://static.wikia.nocookie.net/fortnite/images/c/cf/Gold_III_-_Icon_-_Fortnite.png/revision/latest/scale-to-width-down/100?cb=20230531201231",
    "platinum i": "https://static.wikia.nocookie.net/fortnite/images/2/2a/Platinum_I_-_Icon_-_Fortnite.png/revision/latest/scale-to-width-down/100?cb=20230531201232",
    "platinum ii": "https://static.wikia.nocookie.net/fortnite/images/3/3e/Platinum_II_-_Icon_-_Fortnite.png/revision/latest/scale-to-width-down/100?cb=20230531201233",
    "platinum iii": "https://static.wikia.nocookie.net/fortnite/images/3/30/Platinum_III_-_Icon_-_Fortnite.png/revision/latest/scale-to-width-down/100?cb=20230531201234",
    "diamond i": "https://static.wikia.nocookie.net/fortnite/images/9/98/Diamond_I_-_Icon_-_Fortnite.png/revision/latest/scale-to-width-down/100?cb=20230531201224",
    "diamond ii": "https://static.wikia.nocookie.net/fortnite/images/d/db/Diamond_II_-_Icon_-_Fortnite.png/revision/latest/scale-to-width-down/100?cb=20230531201226",
    "diamond iii": "https://static.wikia.nocookie.net/fortnite/images/e/e1/Diamond_III_-_Icon_-_Fortnite.png/revision/latest/scale-to-width-down/100?cb=20230531201227",
    "elite": "https://static.wikia.nocookie.net/fortnite/images/2/2e/Elite_-_Icon_-_Fortnite.png/revision/latest/scale-to-width-down/100?cb=20230531201228",
    "champion": "https://static.wikia.nocookie.net/fortnite/images/2/2a/Champion_-_Icon_-_Fortnite.png/revision/latest/scale-to-width-down/100?cb=20230531201223",
    "unreal": "https://static.wikia.nocookie.net/fortnite/images/6/6c/Unreal_-_Icon_-_Fortnite.png/revision/latest/scale-to-width-down/100?cb=20230531201239",
}


def in_fortnite_role(member):
    """ Return True if the member is part of the "fortnite"
    Discord role, otherwise False
    """
    return any(x.name == FORTNITE_DISCORD_ROLE for x in member.roles)


def joined_fortnite_voice_channel(before_voice_state, after_voice_state):
    """ Return True if the channel joined is the Fortnite
    voice chat
    """
    channel_before = before_voice_state.channel.name if before_voice_state.channel else None
    channel_after = after_voice_state.channel.name if after_voice_state.channel else None

    switched_channel = channel_before != channel_after
    joined_fortnite_channel = channel_after == FORTNITE_DISCORD_VOICE_CHANNEL_NAME

    return switched_channel and joined_fortnite_channel


def left_fortnite_voice_channel(before_voice_state, after_voice_state):
    channel_before = before_voice_state.channel.name if before_voice_state.channel else None
    channel_after = after_voice_state.channel.name if after_voice_state.channel else None

    in_fortnite_channel = channel_before == FORTNITE_DISCORD_VOICE_CHANNEL_NAME
    return in_fortnite_channel and channel_after is None


def is_first_joiner_of_channel(voice_state):
    """ Return True if the member is the only person in the
    voice channel, otherwise False
    """
    return len(voice_state.channel.members) == 1


def get_season_id():
    """ Returns the latest season ID that the bot knows of """
    return int(os.getenv("FORTNITE_SEASON_ID"))


def create_stats_message(title, desc, color_metric, create_stats_func, stats_breakdown, rank_name, rank_progress, username=None, twitch_stream=None):
    """ Create Discord message """
    message_params = _create_stats_message_params(title, desc, color_metric, username)

    message = discord.Embed(**message_params)

    for mode in MODES:
        if mode not in stats_breakdown:
            continue

        if mode == "all":
            name = "Overall"
        else:
            name = mode.capitalize()

        message.add_field(name=f"[{name}]", value=create_stats_func(mode, stats_breakdown), inline=False)

    if twitch_stream:
        message.add_field(name="[Twitch]", value=twitch_stream, inline=False)

    if rank_name:
        message.add_field(name="[Rank]", value=rank_name + f" - {rank_progress}%", inline=False)
        message.set_thumbnail(url=RANK_ICONS[rank_name.lower()])

    return message


def _create_stats_message_params(title, desc, color_metric, username):
    """ Create the stats message embed params """
    params = {
        "title": title,
        "description": desc,
        "color": _calculate_skill_color_indicator(color_metric)
    }

    if username:
        params["url"] = _create_account_profile_url(username, get_season_id())

    return params


def _calculate_skill_color_indicator(overall_kd):
    """ Return the skill color indicator """
    if overall_kd >= 5:
        return 0x3a0357
    elif overall_kd >= 4:
        return 0xa600ff
    elif overall_kd >= 3:
        return 0xff0000
    elif overall_kd >= 2:
        return 0xff8800
    elif overall_kd >= 1:
        return 0xffff00
    else:
        return 0xfffffe


def calculate_skill_rate_indicator(overall_kd):
    """ Return the skill rate indicator """
    if overall_kd >= 5:
        return "Hackers"
    elif overall_kd >= 4:
        return "Aim Botters"
    elif overall_kd >= 3:
        return "Sweats"
    elif overall_kd >= 2:
        return "High"
    elif overall_kd >= 1:
        return "Medium"
    else:
        return "Bots"


def create_wins_str(wins, matches):
    """ Create opponent stats string for output """
    wins_str = int(wins)
    matches_str = int(matches)
    return f"Wins: {wins_str} / {matches_str} played"


def _create_account_profile_url(username, season_id):
    """ Create the FN Tracker profile URL """
    return ACCOUNT_PROFILE_URL.format(
        username=quote(username),
        season=season_id)
