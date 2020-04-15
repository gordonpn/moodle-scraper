import os
import subprocess
import time
from subprocess import PIPE, STDOUT
from typing import List
from logging.config import fileConfig
import logging

logging.config.fileConfig("logging.ini")
logger = logging.getLogger(__name__)


class PDFConverter:
    def __init__(self, course_paths_lists: List[str] = None):
        self.files_to_remove: List[str] = []
        self.course_paths_list = course_paths_lists

    def run(self):
        self.convert_to_pdf()
        self.clean_duplicates()

    def convert_to_pdf(self) -> None:
        for course_path in self.course_paths_list:
            for file_ in os.listdir(course_path):
                if file_.endswith(".ppt"):
                    process = subprocess.Popen(
                        ["libreoffice", "--headless", "--convert-to", "pdf", file_],
                        cwd=course_path + "/",
                        stdout=PIPE,
                        stderr=STDOUT,
                    )
                    for line in process.stdout:
                        logger.debug(line)
                    self.files_to_remove.append(course_path + "/" + file_)

    def clean_duplicates(self):
        time.sleep(60)
        for file_ in self.files_to_remove:
            logger.debug(f"Removing {file_}")
            os.remove(file_)
