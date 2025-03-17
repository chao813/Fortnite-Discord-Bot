import asyncio
import os
import time
from pprint import pprint

from core.config import config
from core.clients.fortnite_api import (
    _get_player_account_info,
    _get_player_latest_season_stats,
    _get_player_rank
)


async def main():
    start_time = time.perf_counter()

    await test_player_stats()

    elapsed_time = time.perf_counter() - start_time
    print(f"Elapsed time: {elapsed_time:.1f} sec")


async def test_player_stats():
    player_name = os.environ["FORTNITE_TEST_PLAYER"]
    print(f"Player name: {player_name}")

    game_mode = config["fortnite"]["game_mode_for_stats"]
    print(f"Game mode: {game_mode}")

    account_info = await _get_player_account_info(player_name)

    print("Account info")
    pprint(account_info)

    player_stats, player_rank = await asyncio.gather(
        _get_player_latest_season_stats(account_info),
        _get_player_rank(account_info)
    )

    print("Player stats")
    pprint(player_stats)

    print("Player rank")
    pprint(player_rank)


if __name__ == "__main__":
    asyncio.run(main())
