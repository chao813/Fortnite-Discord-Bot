import logging
import contextvars
import uuid
from functools import wraps

from flask import request, g, Flask, Response

# Context variable to track the source or context of each log message
DISCORD_IDENTIFIER = contextvars.ContextVar("discord_identifier", default="")


class IdentifierFormatter(logging.Formatter):
    """Formatter that includes the identifier from either the Discord context
    or a custom value from the Flask workflow."""

    def format(self, record):
        if not hasattr(record, "identifier"):
            identifier = DISCORD_IDENTIFIER.get()
            record.identifier = f" [{identifier}]" if identifier else ""
        return super().format(record)


def configure_logger():
    """Set up logging with the Discord formatter"""
    formatter = IdentifierFormatter(
        "[%(asctime)s] %(levelname)s [%(name)s]%(identifier)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    warn_level_loggers = [
        "discord",
        # "requests"
    ]

    for logger_name in warn_level_loggers:
        lib_logger = logging.getLogger(logger_name)
        lib_logger.setLevel(logging.WARNING)


def get_logger_with_context(name="flask.app", identifier=None):
    """Get a logger with context identifier if provided."""
    logger = logging.getLogger(name)

    if identifier:
        # If an identifier was explicitly provided, temporarily set it for this log
        token = DISCORD_IDENTIFIER.set(identifier)
        # Reset after getting the logger (the identifier will be captured in the log record)
        DISCORD_IDENTIFIER.reset(token)

    return logger


def log_command(func):
    """Decorator that sets up logging context for commands"""
    @wraps(func)
    async def wrapper(ctx, *args, **kwargs):
        identifier = _get_identifier_from_context(ctx)
        token = DISCORD_IDENTIFIER.set(identifier)

        cmd_prefix = ctx.prefix if hasattr(ctx, "prefix") else "!"
        cmd_text = _recreate_discord_command_text(ctx, cmd_prefix, args, kwargs)

        logger = logging.getLogger("discord.commands")
        logger.info("Command called: '%s'", cmd_text)

        try:
            return await func(ctx, *args, **kwargs)
        except Exception as e:
            logger.error("Error executing command '%s': %s", ctx.invoked_with, str(e), exc_info=True)
            raise
        finally:
            DISCORD_IDENTIFIER.reset(token)

    return wrapper


def _get_identifier_from_context(ctx):
    """Construct the identifier from context."""
    server = ctx.guild.name if ctx.guild else "DM"
    author = ctx.author
    return f"{server}:{author}"


def _recreate_discord_command_text(ctx, cmd_prefix, args, kwargs):
    """Recreate the Discord command invoked."""
    cmd_text = f"{cmd_prefix}{ctx.invoked_with}"

    if args:
        args_str = " ".join(str(arg) for arg in args)
        cmd_text += f" {args_str}"

    if kwargs:
        kwargs_str = " ".join(f"{k}={v}" for k, v in kwargs.items())
        cmd_text += f" {kwargs_str}"

    return cmd_text


def log_event(identifier="Main"):
    """Decorator for events to set a default context identifier.
    If used as @log_event, then the identifier will be set to "Main".
    If used as @log_event("Custom"), then the identifier will be set
    to "Custom".
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            token = DISCORD_IDENTIFIER.set(identifier)

            try:
                return await func(*args, **kwargs)
            finally:
                DISCORD_IDENTIFIER.reset(token)

        return wrapper

    if callable(identifier):
        # When an identifier is not provided in the decorator,
        # identifier here is actually the decorated function
        f = identifier
        identifier = "Main"
        return decorator(f)
    return decorator


# Flask Request Logging Integration
def initialize_request_logger(app):
    """Initialize Flask request logger"""
    app.before_request(_generate_request_id)
    app.before_request(_log_request)
    app.after_request(_log_response)


def _generate_request_id():
    """Generate a short 8 character request ID"""
    g.request_id = str(uuid.uuid4())[:8]


def _log_request():
    """Log Flask request details"""
    if _is_healthcheck():
        return

    log_id = f"request:{g.request_id}"
    logger = get_logger_with_context("flask.request", log_id)

    request_data = {
        "name": "request_log",
        "request_id": g.request_id,
        "method": request.method,
        "url": request.url,
        "path": request.path,
        "remote_addr": request.remote_addr,
    }

    # Only include request data for non-GET requests
    if request.method != "GET" and request.data:
        request_data["data"] = _decode_to_text(request.data)

    logger.info(request_data)


def _log_response(response):
    """Log Flask response details"""
    if _is_healthcheck():
        return response

    log_id = f"request:{g.request_id}"
    logger = get_logger_with_context("flask.response", log_id)

    response_data = {
        "name": "response_log",
        "request_id": g.request_id,
        "status": response.status_code,
    }

    # Only include response data if it's not too large (to prevent huge log entries)
    if response.data and len(response.data) < 10000:  # Limit to ~10KB
        response_data["data"] = _decode_to_text(response.data)

    logger.info(response_data)
    return response


def _is_healthcheck():
    """Returns True if the request is a healthcheck request"""
    return request.path == "/fortnite/healthcheck"


def _decode_to_text(data):
    """Decode response data to text when applicable.
    If a character cannot be decoded, then replace it with a valid placeholder.
    """
    if data:
        return data.decode("utf-8", errors="replace")
    return ""
