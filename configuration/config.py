import logging
from configparser import ConfigParser
from typing import List

logger = logging.getLogger("moodle_scraper")


class Config:
    CONFIG_FILE: str = "excluded_courses.ini"

    def __init__(self):
        self.excluded_courses: List[str] = []

    def get_config(self):
        config_parser: ConfigParser = ConfigParser()
        config_parser.read(Config.CONFIG_FILE)

        try:
            self.excluded_courses: List[str] = self._get_exclusions(config_parser)

        except Exception as e:
            logger.error(f"Error with config file format | {str(e)}")
            raise SyntaxError

    def _get_exclusions(self, config_parser: ConfigParser) -> List[str]:
        exclusions: List[str] = []
        if config_parser.has_option("moodle-scraper", "exclusions"):
            exclusions_text = config_parser.get("moodle-scraper", "exclusions")
            if not exclusions_text:
                logger.info(
                    f"No user defined course exclusions found in {Config.CONFIG_FILE}"
                )
            else:
                exclusions = exclusions_text.lower().split(",")
                exclusions = [text.strip() for text in exclusions]
                logger.info(
                    f"User defined course exclusions found in {Config.CONFIG_FILE}:"
                )
                for text in exclusions:
                    logger.info(f"{text}")
        return exclusions
