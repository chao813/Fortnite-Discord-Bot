import os

TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")

TWITCH_AUTHENTICATION_URL = "https://id.twitch.tv/oauth2/token?client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials"
TWITCH_STREAM_URL = "https://api.twitch.tv/helix/streams?game_id={game_id}&first=100&user_login={user_login}"
TWITCH_GAME_URL = "https://api.twitch.tv/helix/games?name=Fortnite"


async def get_twitch_stream(username):
    """Get Twitch stream if player is streaming."""
    # TODO: Fix this, this was moved from fortnite_api.py
    # Wrap aiohttp around this and remove session = None
    # Return data in format: "[Streaming here]({twitch_stream})".format(stream_url=twitch_stream)
    return

    session = None

    user_login = username
    if "TTV" in username:
        user_login = username.strip("TTV")
    if "ttv" in username:
        user_login = username.strip("ttv")

    twitch_auth_response = await session.post(TWITCH_AUTHENTICATION_URL.format(client_id=TWITCH_CLIENT_ID, client_secret=TWITCH_CLIENT_SECRET))
    twitch_bearer_token = await twitch_auth_response.json()

    twitch_game_reponse = await session.get(TWITCH_GAME_URL, headers={"Authorization": "Bearer " + twitch_bearer_token["access_token"], "Client-ID": TWITCH_CLIENT_ID})
    twitch_game = await twitch_game_reponse.json()

    twitch_stream_response = await session.get(TWITCH_STREAM_URL.format(game_id=twitch_game["data"][0]["id"], user_login=user_login), headers={"Authorization": "Bearer " + twitch_bearer_token["access_token"], "Client-ID": TWITCH_CLIENT_ID})
    twitch_fortnite_streams = await twitch_stream_response.json()

    twitch_stream = ""
    if twitch_stream_response.status == 200 and twitch_fortnite_streams["data"]:
        twitch_stream = "https://www.twitch.tv/{username}".format(username=username)
    return twitch_stream
