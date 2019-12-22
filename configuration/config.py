import os
import sys
from configparser import ConfigParser
from typing import List

from configuration.logger import get_logger


class Config:

    def __init__(self):
        self.username: str = ""
        self.password: str = ""
        self.user_path: str = ""
        self.excluded_courses: List[str] = []
        self.logger = get_logger()

    def get_config(self):
        config_parser: ConfigParser = ConfigParser()
        config_parser.read('moodle-scraper.conf')

        try:
            self.username: str = self._get_username(config_parser)
            self.password: str = self._get_password(config_parser)
            self.user_path: str = self._get_save_folder(config_parser)
            self.excluded_courses: List[str] = self._get_exclusions(config_parser)

        except Exception as e:
            self.logger.error(f"Error with config file format | {str(e)}")
            sys.exit(-1)

    def _get_exclusions(self, config_parser: ConfigParser) -> List[str]:
        exclusions: List[str] = []
        if config_parser.has_option('moodle-scraper', 'exclusions'):
            exclusions_text = config_parser.get('moodle-scraper', 'exclusions')
            if not exclusions_text:
                self.logger.info("No user defined course exclusions found in config file")
            else:
                exclusions = exclusions_text.lower().split(',')
                exclusions = [text.strip() for text in exclusions]
                self.logger.info("User defined course exclusions found in config file:")
                for text in exclusions:
                    self.logger.info(f"{text}")
        return exclusions

    def _get_save_folder(self, config_parser: ConfigParser) -> str:
        custom_path: str = ""
        if config_parser.has_option('moodle-scraper', 'folder'):
            custom_path: str = config_parser.get('moodle-scraper', 'folder')
        if not custom_path:
            custom_path = os.getcwd()
            self.logger.info("Using default folder ")
        else:
            self.logger.info("User defined folder found in config file")
        return custom_path

    def _get_password(self, config_parser: ConfigParser) -> str:
        passwd: str = ""
        if "MOODLE_PASSWORD" in os.environ:
            self.logger.info("Password found in environment variables")
            passwd: str = os.environ["MOODLE_PASSWORD"]
        else:
            if config_parser.has_option('moodle-scraper', 'password'):
                passwd = config_parser.get('moodle-scraper', 'password')
            if not passwd:
                self.logger.error("Password not found in config file")
                sys.exit(-1)
            else:
                self.logger.info("Password found in config file")
        return passwd

    def _get_username(self, config_parser: ConfigParser) -> str:
        user: str = ""
        if "MOODLE_USERNAME" in os.environ:
            self.logger.info("Username found in environment variables")
            user: str = os.environ["MOODLE_USERNAME"]
        else:
            if config_parser.has_option('moodle-scraper', 'username'):
                user = config_parser.get('moodle-scraper', 'username')
            if not user:
                self.logger.error("Username not found in config file")
                sys.exit(-1)
            else:
                self.logger.info("Username found in config file")
        return user
