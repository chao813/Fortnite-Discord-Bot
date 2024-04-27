import os

import aiomysql

from utils.dates import get_playing_session_date


class MySQL:
    """ Super barebone MySQL class """
    @classmethod
    async def create(cls):
        self = MySQL()
        self._conn = await self._instantiate_connection()
        return self

    async def _instantiate_connection(self):
        """ Instantiate MySQL connection """
        params = {
            "host": os.getenv("DATABASE_HOST"),
            "port": int(os.getenv("DATABASE_PORT")),
            "user": os.getenv("DATABASE_USERNAME"),
            "password": os.getenv("DATABASE_PASSWORD"),
            "db": os.getenv("DATABASE_NAME"),
            "charset": "utf8mb4",
            "cursorclass": aiomysql.cursors.DictCursor
        }
        return await aiomysql.connect(**params)

    async def insert_player(self, params):
        """ Insert player into the table """
        query = """INSERT IGNORE INTO players (`username`, `season`, `mode`, `kd`, `games`, `wins`,
                                               `win_rate`, `trn`, `rank_name`, `rank_progress`, `date_added`)
                   VALUES (%(username)s, %(season)s, %(mode)s, %(kd)s, %(games)s, %(wins)s,
                           %(win_rate)s, %(trn)s, %(rank_name)s, %(rank_progress)s, %(date_added)s);
                """
        await self._executemany(query, params)

    async def fetch_player_stats_diff_today(self, username, season):
        """ """
        query = """SELECT *
                   FROM (
                       SELECT DISTINCT
                           *,
                           DENSE_RANK() OVER (PARTITION BY MODE, season ORDER BY date_added DESC) AS date_rank,
                           DENSE_RANK() OVER (PARTITION BY date_added, MODE, season ORDER BY games DESC) AS game_rank
                       FROM
                           players
                       WHERE
                           username = %(username)s
                           AND season = %(season)s
                       ) as latest_stats
                   WHERE game_rank = 1 AND date_rank IN (1, 2);
                """
        params = {
            "username": username,
            "season": season
        }
        return await self._fetch_all(query, params)

    async def fetch_avg_player_stats_today(self):
        """ Fetch avg player stats from the playing session today """
        query = """SELECT MODE, AVG(kd), AVG(games), AVG(wins), AVG(win_rate), AVG(trn)
                   FROM players
                   WHERE date_added = %(date_added)s
                   GROUP BY 1;
                """
        params = {
            "date_added": get_playing_session_date()
        }
        return await self._fetch_all(query, params)

    async def _executemany(self, query, params=None):
        """ Execute SQL query """
        async with self._conn.cursor() as cursor:
            await cursor.executemany(query, params)
            await self._conn.commit()

    async def _fetch_all(self, query, params=None):
        """ Fetch rows from MySQL """
        async with self._conn.cursor() as cursor:
            await cursor.execute(query, params)
            return await cursor.fetchall()
