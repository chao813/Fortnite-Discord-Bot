from dataclasses import dataclass

from bot.bot import bot

from core.config import config


@dataclass
class Guild:
    """ Guild class used by the Context class """
    name: str = None


@dataclass
class FlaskContext:
    """ Flask context for Discord commands """
    guild: Guild = None
    author: str = None
    invoked_with: str = None

    def __post_init__(self):
        if self.guild is None:
            self.guild = Guild()

    async def send(self, content=None, **kwargs):
        """Execute send from the text channel instance instead of through
        the context object which is not available outside of the bot thread.
        """
        text_channel = config["discord"]["text_channel_id"]
        channel = bot.get_channel(text_channel)
        if channel:
            await channel.send(content, **kwargs)
