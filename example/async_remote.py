import argparse
import asyncio
import logging
import os

from samsungtvws.async_remote import SamsungTVWSAsyncRemote
from samsungtvws.remote import SendRemoteKey

logging.basicConfig(level=logging.DEBUG)


def parseargs() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default=os.environ.get("TV_IP", "1.2.3.4"))
    parser.add_argument("--port", type=int, default=8002)
    parser.add_argument("--token", default=os.environ.get("TV_TOKEN"))
    parser.add_argument("--token_file", default="token_file")
    return parser.parse_args()


async def main() -> None:
    args = parseargs()
    tv = SamsungTVWSAsyncRemote(
        host=args.ip,
        port=args.port,
        token=args.token,
        token_file=args.token_file,
    )
    await tv.start_listening()

    # Request app_list
    logging.info(await tv.app_list())

    # Turn off
    await tv.send_command(SendRemoteKey.click("KEY_POWER"))

    # Turn off (FrameTV)
    # await tv.send_command(SendRemoteKey.hold_key("KEY_POWER", 3))
    
    # Rotate Frame TV (with auto rotation mount)
    # 2022/2023 version
    # await tv.send_command(SendRemoteKey.hold_key("KEY_MULTI_VIEW", 3))
    # 2024 version (no documentation, but pair the autorotation mount by holding the top left settings button on the remote for 5-10 seconds)
    # await tv.send_command(SendRemoteKey.hold_key("KEY_HOME", 3))

    await asyncio.sleep(15)

    await tv.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
