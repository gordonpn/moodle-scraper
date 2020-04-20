import logging
import os
import subprocess
from subprocess import PIPE, STDOUT
from typing import List

logger = logging.getLogger("moodle_scraper")


class PDFConverter:
    def __init__(self, directory):
        self.directory = directory
        self.processes_to_kill: List[subprocess.Popen] = []

    def run(self):
        self.convert_to_pdf()
        self.kill_processes()

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
                    self.processes_to_kill.append(process)
                    for line in process.stdout:
                        logger.debug(line)

    def kill_processes(self):
        logger.debug("Cleaning up processes")
        for process in self.processes_to_kill:
            logger.debug(f"Killing {process.pid}")
            process.kill()
