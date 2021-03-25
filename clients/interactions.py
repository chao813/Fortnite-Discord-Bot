import asyncio
import os

import discord

from commands import COMMANDS


FORTNITE_TEXT_CHANNEL_ID = int(os.getenv("FORTNITE_DISCORD_TEXT_CHANNEL_ID"))
YES_EMOJI = "✅"
NO_EMOJI  = "❌"


async def send_commands_list(ctx):
    """ Send the commands list """
    message = discord.Embed(
        title = "Commands list",
        colour = discord.Colour.orange()
    )

    for name, opt in COMMANDS.items():
        message.add_field(
            name=name,
            value=opt["description"],
            inline=False)

    await ctx.send(embed=message)


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
        title = f"Welcome, {discord_name.title()}",
        description = "Get good, noob!",
        colour = discord.Colour.orange()
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
            timeout=300.0,
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
