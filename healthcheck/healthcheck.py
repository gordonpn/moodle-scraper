import logging
import os
from enum import Enum

import requests

logger = logging.getLogger("moodle_scraper")


class Status(Enum):
    SUCCESS = ""
    START = "/start"
    FAIL = "/fail"


class HealthCheck:
    HC_UUID = "HC_UUID"

    @staticmethod
    def ping_status(status: Status = Status.SUCCESS, msg: str = "") -> None:
        if "DEV_RUN" in os.environ:
            return
        if HealthCheck.HC_UUID not in os.environ:
            raise EnvironmentError(f"Missing {HealthCheck.HC_UUID=}")
        url = f"https://hc-ping.com/{os.getenv(HealthCheck.HC_UUID)}{status.value}"
        if not msg:
            requests.get(url)
        else:
            requests.post(url=url, data=msg, headers={"Content-Type": "text/plain"})
