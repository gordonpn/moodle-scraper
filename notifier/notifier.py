import json
import logging
import os
from typing import Dict

import requests

logger = logging.getLogger("moodle_scraper")


class Notifier:
    def __init__(self):
        self.hook = os.getenv("SLACK_NOTIFIER_HOOK")

    def notify(self, msg: str) -> None:
        if "DEV_RUN" in os.environ:
            return
        wrapped_msg: str = f"moodle-scraper project:\n{msg}"
        slack_data: Dict[str, str] = {"text": wrapped_msg}

        response = requests.post(
            url=self.hook,
            data=json.dumps(slack_data),
            headers={"Content-Type": "application/json"},
        )

        logger_msg = "Message sent to slack notifier webhook"
        if response.ok:
            logger.debug(f"{logger_msg} successful")
        else:
            logger.debug(f"{logger_msg} not successful")
