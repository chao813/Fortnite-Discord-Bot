from dotenv import load_dotenv
load_dotenv()

import argparse
import asyncio
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

    await test_player_stats(player_name)


async def test_player_stats(name):
    print("Getting player info..")
    account_info = await _get_player_account_info(name)
    # print(f"Account Info: {account_info}")
    pprint(account_info)

    print("Getting player stats..")
    player_stats = await _get_player_latest_season_stats(account_info)
    # print(f"Player Stats: {player_stats}")
    pprint(player_stats)

    print("Getting player rank..")
    player_rank = await _get_player_rank(account_info)
    # print(f"Player Rank: {player_rank}")
    pprint(player_rank)


if __name__ == "__main__":
    asyncio.run(main())
