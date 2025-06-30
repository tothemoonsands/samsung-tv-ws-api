#!/usr/bin/env python3
import logging
import os

from dotenv import load_dotenv
from samsungtvws import SamsungTVWS, exceptions


def main() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO)

    ip = os.getenv("TV_IP")
    token = os.getenv("TV_TOKEN")
    if not ip or not token:
        logging.error("Environment variables TV_IP and TV_TOKEN must be set")
        return

    tv = SamsungTVWS(host=ip, port=8002, token=token)
    try:
        tv.art().set_artmode("on")
        logging.info("Art Mode enabled")
    except exceptions.ConnectionFailure as err:
        logging.error("Failed to connect to TV: %s", err)
    except Exception as err:  # noqa: BLE001
        logging.error("Failed to enable Art Mode: %s", err)


if __name__ == "__main__":
    main()
