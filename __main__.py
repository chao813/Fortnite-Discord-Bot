import os
from threading import Thread

from api.app import app
from bot.bot import bot
from core.logger import configure_logger


DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")


def run_flask():
    """ Run Flask service """
    app.run(
        host="0.0.0.0",
        port=5100
    )


if __name__ == "__main__":
    configure_logger()

    # Run Flask service in separate thread
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    # Create Discord bot in main thread
    bot.run(DISCORD_BOT_TOKEN)

    flask_thread.join()
