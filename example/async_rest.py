import argparse
import asyncio
import contextlib
import logging
import os

import aiohttp

from samsungtvws.async_rest import SamsungTVAsyncRest
from samsungtvws.exceptions import HttpApiError

logging.basicConfig(level=logging.DEBUG)


def parseargs() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default=os.environ.get("TV_IP", "1.2.3.4"))
    parser.add_argument("--port", type=int, default=8002)
    parser.add_argument("--token", default=os.environ.get("TV_TOKEN"))
    return parser.parse_args()


async def main() -> None:
    args = parseargs()
    async with aiohttp.ClientSession() as session:
        with contextlib.suppress(HttpApiError):
            rest_api = SamsungTVAsyncRest(
                host=args.ip,
                port=args.port,
                token=args.token,
                session=session,
            )
            logging.info(await rest_api.rest_device_info())


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
