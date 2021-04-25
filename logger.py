import os
import logging
from logging.handlers import TimedRotatingFileHandler


LOGGER_LEVEL = os.getenv("LOGGER_LEVEL")
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH")


def initialize_flask_logger(app):
    pass


def configure_logger():
    """ Abstract logger setup """
    logging.root.setLevel(LOGGER_LEVEL)

    file_handler = TimedRotatingFileHandler(LOG_FILE_PATH, when="W0", interval=7, backupCount=4)
    stream_handler = logging.StreamHandler()

    formatter = logging.Formatter("[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] [%(identifier)s] %(message)s")
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    logger = logging.getLogger(__name__)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


def get_logger_with_context(ctx=None, identifier=None):
    """ Returns a LoggerAdapter with context """
    if not identifier:
        server = ctx.guild.name
        author = ctx.author
        identifier = f"{server}:{author}"

    extra = {
        "identifier" : identifier
    }
    return logging.LoggerAdapter(logging.getLogger(__name__), extra)


def log_command(func):
    def log_wrapper(*args, **kwargs):
        ctx = args[0]
        logger = get_logger_with_context(ctx)
        logger.info(f"Command '{ctx.invoked_with}' called")
        return func(*args, **kwargs)
    return log_wrapper
