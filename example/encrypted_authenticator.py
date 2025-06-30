import asyncio
import argparse
import logging
import os
from typing import Optional

import aiohttp

from samsungtvws.encrypted.authenticator import SamsungTVEncryptedWSAsyncAuthenticator

logging.basicConfig(level=logging.DEBUG)


def parseargs() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default=os.environ.get("TV_IP", "1.2.3.4"))
    parser.add_argument("--port", type=int, default=8080)
    return parser.parse_args()


async def _get_token(
    host: str, web_session: aiohttp.ClientSession, port: int
) -> tuple[str, str]:
    authenticator = SamsungTVEncryptedWSAsyncAuthenticator(
        host, web_session=web_session, port=port
    )
    await authenticator.start_pairing()
    token: Optional[str] = None
    while not token:
        pin = input("Please enter pin from tv: ")
        token = await authenticator.try_pin(pin)

    session_id = await authenticator.get_session_id_and_close()

    return (token, session_id)


async def main() -> None:
    """Get token."""
    args = parseargs()
    async with aiohttp.ClientSession() as web_session:
        token, session_id = await _get_token(args.ip, web_session, args.port)
        print(f"Token: '{token}', session: '{session_id}'")


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
