class ConfigParseError(Exception):
    """ Invalid config syntax error """


class UserDoesNotExist(Exception):
    """ User does not exist """


class UserStatisticsNotFound(Exception):
    """ User statistics not found (ex: private, invalid ID) """


class NoSeasonDataError(Exception):
    """ No season data found """


class NoRankedDataError(Exception):
    """ No ranked data found """
