import logging
import sys


def configure_logging(debug: bool) -> None:
    log_level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        level=log_level,
        format=("%(asctime)s %(levelname)s %(name)s %(message)s"),
        stream=sys.stdout,
    )
