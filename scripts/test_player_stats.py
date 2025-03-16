import argparse
import asyncio
import os
import time
from pprint import pprint

from clients.fortnite_api import (
    _get_player_account_info,
    _get_player_latest_season_stats,
    _get_player_rank
)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("player_name", type=str)
    args = parser.parse_args()
    player_name = args.player_name

    start_time = time.perf_counter()

    await test_player_stats(player_name)

    elapsed_time = time.perf_counter() - start_time
    print(f"Elapsed time: {elapsed_time:.1f} sec")


async def test_player_stats(name):
    game_mode = os.environ["FORTNITE_GAME_MODE_FOR_STATS"]
    print(f"Game mode: {game_mode}")

    print("Getting player info..")
    account_info = await _get_player_account_info(name)
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
