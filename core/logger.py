import logging
import contextvars
import uuid
from functools import wraps

from flask import request, g

# Context variable to track the source or context of each log message
IDENTIFIER_CONTEXT = contextvars.ContextVar("identifier_context", default="")


class IdentifierFormatter(logging.Formatter):
    """Formatter that includes the identifier from either the Discord context
    or custom value manually set for Flask.
    """
    def format(self, record):
        if not hasattr(record, "identifier"):
            identifier = IDENTIFIER_CONTEXT.get()
            record.identifier = f" [{identifier}]" if identifier else ""
        return super().format(record)


def configure_logger():
    """Set up logging with the IdentifierFormatter."""
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
        "werkzeug"
    ]

    for logger_name in warn_level_loggers:
        lib_logger = logging.getLogger(logger_name)
        lib_logger.setLevel(logging.WARNING)


def log_command(func):
    """Decorator that sets up logging context for commands"""
    @wraps(func)
    async def wrapper(ctx, *args, **kwargs):
        identifier = _get_identifier_from_context(ctx)
        token = IDENTIFIER_CONTEXT.set(identifier)

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
            IDENTIFIER_CONTEXT.reset(token)

    return wrapper


def log_event(identifier="Main"):
    """Decorator for events to set a default context identifier.
    If used as @log_event, then the identifier will be set to "Main".
    If used as @log_event("Custom"), then the identifier will be set
    to "Custom".
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            token = IDENTIFIER_CONTEXT.set(identifier)

            try:
                return await func(*args, **kwargs)
            finally:
                IDENTIFIER_CONTEXT.reset(token)

        return wrapper

    if callable(identifier):
        # When an identifier is not provided in the decorator,
        # identifier here is actually the decorated function
        f = identifier
        identifier = "Main"
        return decorator(f)
    return decorator


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


def initialize_request_logger(app):
    """Initialize Flask request logger with request ID tracking."""
    app.before_request(_generate_request_id)
    app.before_request(_log_request)
    app.after_request(_log_response)
    app.teardown_request(reset_request_context)


def reset_request_context(_):
    """Reset the request context identifier at the end of each request."""
    try:
        if hasattr(g, "identifier_token"):
            IDENTIFIER_CONTEXT.reset(g.identifier_token)
    except Exception as exc:
        logger = logging.getLogger("flask.error")
        logger.error("Error resetting context: %s", exc)


def _generate_request_id():
    """Generate a short 8 character request ID."""
    g.request_id = str(uuid.uuid4())[:8]
    token = IDENTIFIER_CONTEXT.set(f"req:{g.request_id}")
    g.identifier_token = token


def _log_request():
    """Log Flask request details."""
    if _is_healthcheck():
        return

    logger = logging.getLogger("flask.request")

    request_data = {
        "method": request.method,
        "url": request.url,
        "path": request.path,
    }

    # Only include request data for non-GET requests
    if request.method != "GET" and request.data:
        request_data["data"] = _decode_to_text(request.data)

    logger.info(request_data)


def _log_response(response):
    """Log Flask response details."""
    if _is_healthcheck():
        return response

    logger = logging.getLogger("flask.response")

    response_data = {
        "status": response.status_code
    }

    # Only include response data if it's not too large
    if response.data and len(response.data) < 10000:
        response_data["data"] = _decode_to_text(response.data)

    logger.info(response_data)

    return response


def _is_healthcheck():
    """Returns True if the request is a healthcheck request."""
    return request.path == "/fortnite/healthcheck"


def _decode_to_text(data):
    """Decode response data to text when applicable.
    If a character cannot be decoded, then replace it with a valid placeholder.
    """
    if data:
        return data.decode("utf-8", errors="replace")
    return ""
