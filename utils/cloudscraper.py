import asyncio
from enum import Enum

import cloudscraper


class Method(Enum):
    """ Supported Cloudscrape methods. All request methods are
    technically supported.
    """
    GET = "get"


async def cloudscrape(method, url, headers, allow_redirects=True):
    """ Cloudscraper is used to bypass Cloudflare's bot detection.
    However, Cloudscraper does not support async so event loops used used.
    """
    def _method():
        scraper = cloudscraper.create_scraper()
        func = getattr(scraper, method.value)
        return func(url, headers=headers, allow_redirects=allow_redirects)

    return await asyncio.get_event_loop().run_in_executor(
        executor=None,
        func=_method
    )
