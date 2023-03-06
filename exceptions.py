class UserDoesNotExist(Exception):
    """ User does not exist """
    pass


class UserStatisticsNotFound(Exception):
    """ User statistics not found (ex: private, invalid ID) """
    pass


class NoSeasonDataError(Exception):
    """ No season data found """
    pass
