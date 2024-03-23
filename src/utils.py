import os
import logging


def find_root_directory():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    while True:
        # Check if we've reached the root directory
        if current_dir == os.path.dirname(current_dir):
            return current_dir
        # Check if 'src' directory exists
        if "src" in os.listdir(current_dir):
            return current_dir
        # Move up one directory
        current_dir = os.path.dirname(current_dir)


def set_loggers_level(level=logging.DEBUG):
    loggers = [
        "scrapy.utils.log",
        "scrapy.crawler",
        "scrapy.middleware",
        "scrapy.core.engine",
        "scrapy.extensions.logstats",
        "scrapy.extensions.telnet",
        "scrapy.core.scraper",
        "scrapy.statscollectors",
    ]
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        for handler in logger.handlers:
            handler.setLevel(level)
