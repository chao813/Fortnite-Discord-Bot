from datetime import datetime, timedelta


def get_playing_session_date():
    """ Get the playing session date.

    A playing session includes the current day and 3 hours
    into midnight in Pacific Time. For example, these all
    count as the same day:
        - 11:00 pm
        - 02:00 am

    The server is in Pacific Time.
    """
    time_now = datetime.now()
    if time_now.hour < 3:
        time_now -= timedelta(days=1)
    return time_now.strftime("%Y-%m-%d")
