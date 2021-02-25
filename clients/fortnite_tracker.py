import requests


ACCOUNT_SEARCH_URL = "https://search-api.tracker.network/search/fortnite?advanced=1&q={username}"
ACCOUNT_PROFILE_URL = "https://fortnitetracker.com/profile/all/{username}?season={season}"

HEADERS = {
    "origin": "https://fortnitetracker.com/",
    "referer": "https://fortnitetracker.com/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36"
}

async def get_username(player_name):
    """ Returns the player's username, or None if not found.
    """
    url = ACCOUNT_SEARCH_URL.format(username=player_name)
    r = requests.get(url, headers=HEADERS).json()
    return r[0]["name"] if r else None

async def get_player_stats(ctx, username):
    page_html = _get_player_profile_html(username)

    # TODO: Parse

def _get_player_profile_html(username):
    url = ACCOUNT_PROFILE_URL.format(username=username, season=_get_latest_season_id())
    response = requests.get(url, headers=HEADERS).text


def _get_latest_season_id():
    """ TODO: Parse dropdown
    """
    return 15
  
