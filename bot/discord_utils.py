from urllib.parse import quote

import discord

from core.config import config


ACCOUNT_PROFILE_URL = "https://fortnitetracker.com/profile/all/{username}?season={season}"

FORTNITE_DISCORD_ROLE = config["discord"]["role"]
FORTNITE_DISCORD_VOICE_CHANNEL_NAME = config["discord"]["voice_channel_name"]

MODES = [
    "solo",
    "duos",
    "trios",
    "squads",
    "all"
]

RANK_ICONS_URL = "https://static.wikia.nocookie.net/fortnite/images"
RANK_ICONS_SIZE_PARAM = "/revision/latest/scale-to-width-down/100"
RANK_ICONS_PATH = {
    "Unranked": "/0/0d/Unknown_Rank_-_Icon_-_Fortnite.png",
    "Bronze I": "/4/44/Bronze_I_-_Icon_-_Fortnite.png",
    "Bronze II": "/9/92/Bronze_II_-_Icon_-_Fortnite.png",
    "Bronze III": "/7/74/Bronze_III_-_Icon_-_Fortnite.png",
    "Silver I": "/c/c3/Silver_I_-_Icon_-_Fortnite.png",
    "Silver II": "/1/1d/Silver_II_-_Icon_-_Fortnite.png",
    "Silver III": "/0/0a/Silver_III_-_Icon_-_Fortnite.png",
    "Gold I": "/3/37/Gold_I_-_Icon_-_Fortnite.png",
    "Gold II": "/f/fb/Gold_II_-_Icon_-_Fortnite.png",
    "Gold III": "/c/cf/Gold_III_-_Icon_-_Fortnite.png",
    "Platinum I": "/2/2a/Platinum_I_-_Icon_-_Fortnite.png",
    "Platinum II": "/3/3e/Platinum_II_-_Icon_-_Fortnite.png",
    "Platinum III": "/3/30/Platinum_III_-_Icon_-_Fortnite.png",
    "Diamond I": "/9/98/Diamond_I_-_Icon_-_Fortnite.png",
    "Diamond II": "/d/db/Diamond_II_-_Icon_-_Fortnite.png",
    "Diamond III": "/e/e1/Diamond_III_-_Icon_-_Fortnite.png",
    "Elite": "/2/2e/Elite_-_Icon_-_Fortnite.png",
    "Champion": "/2/2a/Champion_-_Icon_-_Fortnite.png",
    "Unreal": "/6/6c/Unreal_-_Icon_-_Fortnite.png"
}


def in_fortnite_role(member):
    """ Return True if the member is part of the "fortnite"
    Discord role, otherwise False
    """
    return any(x.name == FORTNITE_DISCORD_ROLE for x in member.roles)


def joined_fortnite_voice_channel(before_voice_state, after_voice_state):
    """ Return True if the channel joined is the Fortnite
    voice chat, otherwise False
    """
    channel_before = before_voice_state.channel.name if before_voice_state.channel else None
    channel_after = after_voice_state.channel.name if after_voice_state.channel else None

    switched_channel = channel_before != channel_after
    joined_fortnite_channel = channel_after == FORTNITE_DISCORD_VOICE_CHANNEL_NAME

    return switched_channel and joined_fortnite_channel


def left_fortnite_voice_channel(before_voice_state, after_voice_state):
    channel_before = before_voice_state.channel.name if before_voice_state.channel else None
    channel_after = after_voice_state.channel.name if after_voice_state.channel else None

    was_in_fortnite_channel = channel_before == FORTNITE_DISCORD_VOICE_CHANNEL_NAME
    left_voice_channel = channel_after is None
    return was_in_fortnite_channel and left_voice_channel


def is_first_joiner_of_channel(voice_state):
    """ Return True if the member is the only person in the
    voice channel, otherwise False
    """
    return len(voice_state.channel.members) == 1


def get_season_id():
    """ Returns the latest season ID that the bot knows of """
    return config["fortnite"]["season_id"]


def create_stats_message(title, desc, color_metric, create_stats_func, stats_breakdown, rank_name=None, rank_progress=None, username=None, twitch_stream=None, meta_info=None):
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

    if rank_name and rank_progress:
        icons_url = f"{RANK_ICONS_URL}{RANK_ICONS_PATH[rank_name]}{RANK_ICONS_SIZE_PARAM}"
        message.add_field(name="[Rank]", value=rank_name + f" - {rank_progress}%", inline=False)
        message.set_thumbnail(url=icons_url)

    if twitch_stream:
        message.add_field(name="[Twitch]", value=twitch_stream, inline=False)

    if meta_info:
        message.add_field(name="[Analysis]", value=meta_info["skills_indicator"], inline=False)
        if (ranks_breakdown := meta_info["ranks_breakdown_ordered"]):
            message.add_field(name="[Ranks Breakdown]", value=ranks_breakdown, inline=False)

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
    """ Return the skill color indicator.
    KD thresholds are calibrated for ranked play as the overall stats
    returned by the API are not broken out by ranked vs unranked playlists.
    """
    if overall_kd >= 2.25:
        return 0x3a0357
    elif overall_kd >= 2.00:
        return 0xa600ff
    elif overall_kd >= 1.75:
        return 0xff0000
    elif overall_kd >= 1.50:
        return 0xff8800
    elif overall_kd >= 1.25:
        return 0xffff00
    else:
        return 0xfffffe


def calculate_skill_rate_indicator(overall_kd):
    """ Return the skill rate indicator.
    KD thresholds are calibrated for ranked play as the overall stats
    returned by the API are not broken out by ranked vs unranked playlists.
    """
    if overall_kd >= 2.25:
        return "Hackers"
    elif overall_kd >= 2.00:
        return "Aim Botters"
    elif overall_kd >= 1.75:
        return "Sweats"
    elif overall_kd >= 1.50:
        return "High"
    elif overall_kd >= 1.25:
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
