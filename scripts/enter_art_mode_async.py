#!/usr/bin/env python3
"""Async script to enable Art Mode on a Samsung Frame TV."""
import asyncio
import logging
import os

from dotenv import load_dotenv

from samsungtvws import exceptions
from samsungtvws.async_art import ArtChannelEmitCommand, SamsungTVAsyncArt


async def main() -> None:
    """Connect to the TV and enable Art Mode."""
    load_dotenv()
    logging.basicConfig(level=logging.INFO)

    ip = os.getenv("TV_IP")
    token = os.getenv("TV_TOKEN")
    if not ip or not token:
        logging.error("Environment variables TV_IP and TV_TOKEN must be set")
        return

    tv = SamsungTVAsyncArt(host=ip, port=8002, token=token)
    try:
        await tv.open()
        logging.info("Connected to TV")
    except exceptions.UnauthorizedError:
        logging.error("Unauthorized. Check TV_TOKEN")
        return
    except exceptions.ConnectionFailure as err:
        logging.error("TV not reachable: %s", err)
        return
    except Exception as err:  # noqa: BLE001
        logging.error("Failed to connect to TV: %s", err)
        return

    try:
        if await tv.in_artmode():
            logging.info("TV is already in Art Mode.")
            return
        await tv.set_artmode("on")
        logging.info("Art Mode ON request sent.")
    except Exception as err:  # noqa: BLE001
        logging.error("Failed to enable Art Mode: %s", err)
        try:
            power = await tv.on()
            logging.info("TV power state: %s", power)
        except Exception:  # noqa: BLE001
            logging.debug("Unable to query power status")
        try:
            await tv.send_command(
                ArtChannelEmitCommand.art_app_request(
                    {"request": "set_artmode_status", "value": "on"}
                )
            )
            logging.info("Fallback Art Mode command sent.")
        except Exception:  # noqa: BLE001
            logging.debug("Fallback command failed")
    finally:
        await tv.close()


if __name__ == "__main__":
    asyncio.run(main())
