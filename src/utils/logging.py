from __future__ import annotations

import logging


def configure_logging(debug: bool = False) -> None:
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO, format="%(message)s")


def stage(name: str, message: str) -> None:
    logging.info("[%s] %s", name, message)
