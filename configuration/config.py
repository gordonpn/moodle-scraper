import os
import sys
from configparser import ConfigParser
from typing import List
from logging.config import fileConfig
import logging

logging.config.fileConfig("logging.ini")
logger = logging.getLogger(__name__)


class Config:
    def __init__(self):
        self.excluded_courses: List[str] = []

    def get_config(self):
        config_parser: ConfigParser = ConfigParser()
        config_parser.read("excluded_courses.ini")

        try:
            self.excluded_courses: List[str] = self._get_exclusions(config_parser)

        except Exception as e:
            logger.error(f"Error with config file format | {str(e)}")
            sys.exit(-1)

    def _get_exclusions(self, config_parser: ConfigParser) -> List[str]:
        exclusions: List[str] = []
        if config_parser.has_option("moodle-scraper", "exclusions"):
            exclusions_text = config_parser.get("moodle-scraper", "exclusions")
            if not exclusions_text:
                logger.info("No user defined course exclusions found in config file")
            else:
                exclusions = exclusions_text.lower().split(",")
                exclusions = [text.strip() for text in exclusions]
                logger.info("User defined course exclusions found in config file:")
                for text in exclusions:
                    logger.info(f"{text}")
        return exclusions
