import logging
import os

import requests

logger = logging.getLogger("moodle_scraper")


class HealthCheck:
    @staticmethod
    def start():
        if "DEV_RUN" in os.environ:
            return
        logger.debug("Sending success health check")
        requests.get(f"https://hc-ping.com/{os.getenv('HC_UUID')}/start")

    @staticmethod
    def success():
        if "DEV_RUN" in os.environ:
            return
        logger.debug("Sending success health check")
        requests.get(f"https://hc-ping.com/{os.getenv('HC_UUID')}")

    @staticmethod
    def fail():
        if "DEV_RUN" in os.environ:
            return
        logger.debug("Sending failed health check")
        requests.get(f"https://hc-ping.com/{os.getenv('HC_UUID')}/fail")
