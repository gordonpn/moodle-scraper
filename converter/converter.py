import logging
import os
import subprocess
import time
from subprocess import PIPE, STDOUT
from typing import List

logger = logging.getLogger("moodle_scraper")


class PDFConverter:
    def __init__(self, directory):
        self.directory = directory
        self.files_to_remove: List[str] = []

    def run(self):
        self.convert_to_pdf()
        # self.clean_duplicates()

    def convert_to_pdf(self) -> None:
        path: str = self.directory

        if not path:
            logger.debug(
                "Saving directory not specified, using current working directory"
            )
            path = f"{os.getcwd()}/courses"
            logger.debug(path)

        for root, dirs, files in os.walk(path):
            for file_ in files:
                if file_.endswith(".ppt"):
                    process = subprocess.Popen(
                        ["libreoffice", "--headless", "--convert-to", "pdf", file_],
                        cwd=f"{root}/",
                        stdout=PIPE,
                        stderr=STDOUT,
                    )
                    for line in process.stdout:
                        logger.debug(line)
                    self.files_to_remove.append(f"{os.path.join(root, file_)}")

    def clean_duplicates(self):
        time.sleep(60)
        for file_ in self.files_to_remove:
            logger.debug(f"Removing {file_}")
            os.remove(file_)
