import logging
import os
import sys

sys.path.append("../")

from samsungtvws import SamsungTVWS  # noqa: E402

# Increase debug level
logging.basicConfig(level=logging.INFO)

ip = os.environ.get("TV_IP", "192.168.xxx.xxx")

# Normal constructor
tv = SamsungTVWS(ip)

# Set all mats to this type
target_matte_type = "none"

# Is art mode supported?
if not tv.art().supported():
    logging.error("Art mode not supported")
    sys.exit(1)

# List available mats for displaying art
matte_types = [
    matte_type for elem in tv.art().get_matte_list() for matte_type in elem.values()
]

if target_matte_type not in matte_types:
    logging.error(
        "Invalid matte type: {}. Supported matte types are: {}".format(
            target_matte_type, matte_types
        )
    )
    sys.exit(1)

# List the art available on the device
available_art = tv.art().available()

for art in available_art:
    try:
        if art["matte_id"] != target_matte_type:
            logging.info(
                "Setting matte to {} for {}".format(target_matte_type, art["content_id"])
            )
            tv.art().change_matte(art["content_id"], target_matte_type)
    except KeyError:
        logging.warning('no mat for {}'.format(art))
