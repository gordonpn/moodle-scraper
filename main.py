import argparse
import logging
import time
from contextlib import ContextDecorator
from logging.config import fileConfig

import schedule

from converter.converter import PDFConverter
from downloader.downloader import Downloader
from healthcheck.healthcheck import HealthCheck, Status
from notifier.notifier import Notifier

logging.config.fileConfig("logging.ini", disable_existing_loggers=False)
logger = logging.getLogger("moodle_scraper")
notifier: Notifier = Notifier()


def arguments_parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a",
        "--automated",
        action="store_true",
        help="run the moodle scraper on a schedule",
    )
    parser.add_argument(
        "-d",
        "--directory",
        action="store",
        help="specify directory to save files",
        type=str,
        nargs=1,
    )
    parser.add_argument(
        "-u",
        "--username",
        action="store",
        help="your moodle username",
        type=str,
        nargs=1,
    )
    parser.add_argument(
        "-p",
        "--password",
        action="store",
        help="your moodle password",
        type=str,
        nargs=1,
    )
    parser.add_argument(
        "-c",
        "--convert",
        action="store_true",
        help="convert to PDF using LibreOffice after downloading. this option has only been tested on Ubuntu",
    )

    return parser.parse_args()


class Timer(ContextDecorator):
    def __enter__(self):
        msg: str = "Started job"
        logger.debug(msg)
        self.start_time = time.time()
        return self

    def __exit__(self, type_, value, traceback):
        end_time = time.time()
        run_time = end_time - self.start_time
        msg: str = f"Job completed. Total run time: {int(run_time)} seconds"
        logger.debug(msg)


@Timer()
def job():
    try:
        HealthCheck.ping_status(Status.START)
        downloader = Downloader(args.username, args.password, args.directory)
        downloader.run()

        if args.convert:
            converter = PDFConverter(args.directory)
            converter.run()

        HealthCheck.ping_status(Status.SUCCESS)
    except Exception:
        HealthCheck.ping_status(Status.FAIL)
        raise Exception


def run_schedule():
    logger.debug("Setting schedule")
    schedule.every(1).hours.do(job)

    while True:
        schedule.run_pending()
        time.sleep(5 * 60)


if __name__ == "__main__":
    args: argparse.Namespace = arguments_parser()
    job()
    if args.automated:
        run_schedule()
