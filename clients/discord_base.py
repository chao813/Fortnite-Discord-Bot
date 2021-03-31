import os
from urllib.parse import quote

import discord


ACCOUNT_PROFILE_URL = "https://fortnitetracker.com/profile/all/{username}?season={season}"

FORTNITE_DISCORD_ROLE = os.getenv("FORTNITE_DISCORD_ROLE")
FORTNITE_DISCORD_VOICE_CHANNEL_NAME = os.getenv("FORTNITE_DISCORD_VOICE_CHANNEL_NAME")

MODES = [
    "all",
    "solo",
    "duos",
    "squads"
]


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


def is_first_joiner_of_channel(voice_state):
    """ Return True if the member is the only person in the
    voice channel, otherwise False
    """
    return len(voice_state.channel.members) == 1


def get_season_id():
    """ Returns the latest season ID that the bot knows of """
    return int(os.getenv("FORTNITE_SEASON_ID"))


def create_account_profile_url(username, season_id):
    """ Creates the FN Tracker profile URL """
    return ACCOUNT_PROFILE_URL.format(
        username=quote(username),
        season=season_id)


def create_stats_message(title, desc, create_stats_func, stats_breakdown, color, url=None):
    """ Create Discord message """
    message_params = {
        "title": title,
        "url": url,
        "description": desc,
        "color": color
    }

    if url:
        message_params["url"] = url

    # TODO: Pass in dict directly to here
    message = discord.Embed(**message_params)

    for mode in MODES:
        if mode not in stats_breakdown:
            continue

        if mode == "all":
            name = "Overall"
        else:
            name = mode.capitalize()

        message.add_field(name=f"[{name}]", value=create_stats_func(mode, stats_breakdown), inline=False)

    return message


def calculate_skill_color_indicator(overall_kd):
    """ Return the skill color indicator """
    if overall_kd >= 3:
        return 0xa600ff
    elif overall_kd < 3 and overall_kd >= 2:
        return 0xff0000
    elif overall_kd < 2 and overall_kd >= 1:
        return 0xff8800
    else:
        return 0x17b532


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

