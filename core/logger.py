import os
import logging
import uuid
from functools import wraps

from flask import request, g


LOGGER_LEVEL = os.getenv("LOGGER_LEVEL")


def configure_logger():
    """ Abstract logger setup """
    logging.root.setLevel(LOGGER_LEVEL)

    stream_handler = logging.StreamHandler()

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] [%(identifier)s] %(message)s"
    )
    stream_handler.setFormatter(formatter)

    logger = logging.getLogger(__name__)
    logger.addHandler(stream_handler)

    return logger


def get_logger_with_context(ctx=None, identifier=None):
    """ Returns a LoggerAdapter with context """
    if not identifier:
        server = ctx.guild.name
        author = ctx.author
        identifier = f"{server}:{author}"

    extra = {
        "identifier": identifier
    }
    return logging.LoggerAdapter(logging.getLogger(__name__), extra)


def log_command(coro):
    """ Decorator to log Discord bot commands """
    @wraps(coro)
    async def log_wrapper(*args, **kwargs):
        ctx = args[0]
        logger = get_logger_with_context(ctx)
        logger.info(f"Discord command called: '!{ctx.invoked_with}'")
        return await coro(*args, **kwargs)
    return log_wrapper


def initialize_request_logger(app):
    """ Initialize Flask request logger """
    app.before_request(_generate_request_id)
    app.before_request(_log_request)
    app.after_request(_log_response)


def _generate_request_id():
    """ Generate a short 8 char request ID """
    g.request_id = str(uuid.uuid4())[:8]


def _log_request():
    """ Log Flask request """
    if _is_healthcheck():
        return

    log_id = f"request:{g.request_id}"
    logger = get_logger_with_context(identifier=log_id)

    logger.info({
        "name": "request_log",
        "request_id": g.request_id,
        "data": {
            "method": request.method,
            "url": request.url,
            "data": request.data
        },
    })


def _log_response(response):
    """ Log Flask response """
    if _is_healthcheck():
        return response

    log_id = f"request:{g.request_id}"
    logger = get_logger_with_context(identifier=log_id)

    logger.info({
        "name": "response_log",
        "request_id": g.request_id,
        "data": {
            "status": response.status,
            "data": response.data
        },
    })

    return response


def _is_healthcheck():
    """ Returns True if the request is a healthcheck request """
    # return request.path == "/fortnite/healthcheck"
    return False
