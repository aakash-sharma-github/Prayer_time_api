import logging
import sys


def configure_logging(log_level: str) -> None:
    resolved_log_level = getattr(logging, log_level, logging.INFO)
    if not isinstance(resolved_log_level, int):
        resolved_log_level = logging.INFO

    logging.basicConfig(
        level=resolved_log_level,
        format=("%(asctime)s %(levelname)s %(name)s %(message)s"),
        stream=sys.stdout,
    )
