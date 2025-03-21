import asyncio

import discord

import bot.discord_utils as discord_utils
from bot.commands import COMMANDS
from core.config import config


FORTNITE_TEXT_CHANNEL_ID = config["discord"]["text_channel_id"]
WAIT_FOR_TIMEOUT_SEC = 180
YES_EMOJI = "✅"
NO_EMOJI  = "❌"


async def send_commands_list(ctx):
    """ Send the commands list """
    message = discord.Embed(
        title="Commands list",
        colour=discord.Colour.orange()
    )

    for name, opt in COMMANDS.items():
        keywords = ", ".join([opt["command"]] + opt.get("aliases", []))
        examples = opt.get("examples", "")
        usage_desc = f"{opt['description']}\nUsage: {keywords}\nExample: {examples}"

        message.add_field(
            name=name,
            value=usage_desc,
            inline=False)

    await ctx.send(embed=message)


def should_add_player_to_squad_player_session_list(member, before, after):
    """ Return True if player should be added to squad player list,
    otherwise False
    """
    return discord_utils.in_fortnite_role(member) and \
           discord_utils.joined_fortnite_voice_channel(before, after)


def should_remove_player_from_squad_player_session_list(member, before, after):
    """ Return True if player should be removed from current session
    squad player list, otherwise False """
    return discord_utils.in_fortnite_role(member) and \
           discord_utils.left_fortnite_voice_channel(before, after)


def send_track_question(member, before, after):
    """ Return True if the track question should be sent,
    otherwise False
    """
    return discord_utils.in_fortnite_role(member) and \
           discord_utils.joined_fortnite_voice_channel(before, after) and \
           discord_utils.is_first_joiner_of_channel(after)


async def send_track_question_and_wait(bot, discord_name):
    """ Send a question asking if the user wants to see current stats
    for the squad. If yes, return silent=False, otherwise return
    silent=True
    """
    message = await _send_message(bot, discord_name)
    silent_mode = await _wait_for_response(bot, message)
    ctx = await _get_message_context(bot, message)
    return ctx, silent_mode


async def _send_message(bot, discord_name):
    """ Send the question with emojis """
    track_question = discord.Embed(
        title=f"Welcome, {discord_name.title()}",
        description="Get good, noob!",
        colour=discord.Colour.orange()
    )

    track_question.add_field(
        name="Do you want to see the current squad stats?",
        value="Select Yes or No using the emojis below",
        inline=False)

    message = await bot.get_channel(FORTNITE_TEXT_CHANNEL_ID) \
                       .send(embed=track_question)

    await message.add_reaction(YES_EMOJI)
    await message.add_reaction(NO_EMOJI)

    return message


async def _wait_for_response(bot, message):
    """ Wait for emoji reaction and return True if squad stats
    tracking should be ran in silent mode, otherwise False
    """
    def check(_, user):
        """ User must not be the bot """
        return user != message.author

    try:
        reaction, _ = await bot.wait_for(
            "reaction_add",
            timeout=WAIT_FOR_TIMEOUT_SEC,
            check=check)
    except asyncio.TimeoutError:
        reaction = None

    silent_mode = True

    if not reaction:
        return silent_mode

    if str(reaction) == YES_EMOJI:
        silent_mode = False

    return silent_mode


async def _get_message_context(bot, message):
    """ Return the message context """
    return await bot.get_context(message)


async def send_upgrade_locations(ctx):
    """ Send map of upgrade locations """
    await ctx.send("https://www.escapistmagazine.com/wp-content/uploads/2023/12/fortnite-all-vault-and-bunker-locations.jpg")


async def send_hirable_npc_locations(ctx):
    """ Send map of hireable NPC locations """
    await ctx.send("https://dotesports.com/wp-content/uploads/2024/03/Hireable-NPCS.jpg")


async def send_chest_locations(ctx):
    """ Show map of bunker and regular chest locations """
    chest_location_details = (
        "1 - Inside a tower that’s located toward the northwest corner of the main structure.\n"
        "2 - Buried in a field to the south of Stealthy Stronghold on a small hill, outside of the walls.\n"
        "3 - In the house with a red roof under the staircase toward the western part of the town.\n"
        "4 - In the attic of a house toward the landmark’s west.\n"
        "5 - In the building that’s half covered in sand, and the Bunker chest will be waiting for you in its basement.\n"
        "6 - Southeast of the landmark in the sand.\n"
        "7 - In a small campsite west of the Green Steel Bridge.\n"
        "8 - Head over to the house with storm shelter toward the southeastern corner of the landmark.\n"
        "9 - In the attic of a house, located toward the southeastern part of the town.\n"
        "10 - In a field, east of Flopper Pond.\n"
        "11 - In the shack that’s on the top.\n"
        "12 - Near a road that’s west of Durr Burger.\n"
        "13 - Next to the control panel in a house toward the northern edge of the landmark.\n"
        "14 - In a house on the southwestern edge of the landmark.\n"
        "15 - In the flowery fields toward Retail Row’s west.\n"
        "16 - In a field in between Loot Lake and Lazy Lake.\n"
        "17 - Inside of the attic.\n"
        "18 - In the basement of the house and you’ll need to destroy the floor beneath the table with your harvesting tool to access the room.\n"
        "19 - In the large house in the flower fields, located toward the southwest of Misty Meadows.\n"
        "20 - In a shack.\n"
        "21 - In the crossroads between Sweaty Sand and Holly Hedges.\n"
        "22 - Under the sand along the shore line.\n")
    await ctx.send("https://cdn1.dotesports.com/wp-content/uploads/2021/03/25194519/fortnite-bunker-loc-1024x864.png")
    await ctx.send(f"```{chest_location_details}```")
