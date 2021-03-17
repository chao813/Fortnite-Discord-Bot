from database.mysql import MySQL

async def get_player_stats_today():
    """ """
    mysql = await MySQL.create()
    return await mysql.fetch_avg_player_stats_today()
