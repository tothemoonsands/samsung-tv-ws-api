import argparse
import asyncio
import logging
import os

import aiohttp

from samsungtvws.encrypted.remote import SamsungTVEncryptedWSAsyncRemote, SendRemoteKey

logging.basicConfig(level=logging.DEBUG)


def parseargs() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default=os.environ.get("TV_IP", "1.2.3.4"))
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--token", default=os.environ.get("TV_TOKEN"))
    parser.add_argument("--session_id", default="1")
    return parser.parse_args()


async def main() -> None:
    """Run remote commands."""
    args = parseargs()
    async with aiohttp.ClientSession() as web_session:
        remote = SamsungTVEncryptedWSAsyncRemote(
            host=args.ip,
            web_session=web_session,
            token=args.token,
            session_id=args.session_id,
            port=args.port,
        )
        await remote.start_listening()

        # Turn off
        await remote.send_command(SendRemoteKey.click("KEY_POWEROFF"))

        await asyncio.sleep(15)

        await remote.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
