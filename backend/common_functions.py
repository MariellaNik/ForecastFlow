import codecs
import logging
import sys
from logging.handlers import TimedRotatingFileHandler

import yaml


def parse_config(config_file):
    with codecs.open(config_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def setup_logging(logging_config):
    if not logging_config:
        return

    # Logger
    logger = logging.getLogger("app")
    logger.setLevel(logging.DEBUG)

    # File Handler
    if "file_level" in logging_config and str(
            logging_config["file_level"]
    ).lower() not in ["", "none"]:
        file_handler = TimedRotatingFileHandler(
            logging_config.get("file_path", "logfile.log"), when="midnight"
        )
        file_handler.setLevel(
            getattr(logging, logging_config.get("file_level").upper())
        )
        file_handler.setFormatter(logging.Formatter(logging_config.get("file_format")))
        logger.addHandler(file_handler)

    # Console Handler
    if "console_level" in logging_config and str(
            logging_config["console_level"]
    ).lower() not in ["", "none"]:
        console_handler = logging.StreamHandler(stream=sys.stdout)
        console_handler.setLevel(
            getattr(logging, logging_config.get("console_level").upper())
        )
        console_handler.setFormatter(
            logging.Formatter(logging_config.get("console_format"))
        )
        logger.addHandler(console_handler)

    return logger