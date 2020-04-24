import logging
import os
import subprocess
from subprocess import PIPE, STDOUT, Popen
from threading import Thread
from typing import List

logger = logging.getLogger("moodle_scraper")


class PDFConverter:
    def __init__(self, directory):
        self.directory = directory
        self.processes_to_kill: List[Popen] = []
        self.threads: List[Thread] = []

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
                    t = Thread(target=self._conversion_job,
                               kwargs={"file_to_convert": file_, "root": root})
                    self.threads.append(t)
                    t.start()

    def _conversion_job(self, file_to_convert, root) -> None:
        process = subprocess.Popen(
            ["libreoffice", "--headless", "--convert-to", "pdf", file_to_convert],
            cwd=f"{root}/",
            stdout=PIPE,
            stderr=STDOUT,
        )
        self.processes_to_kill.append(process)
        for line in process.stdout:
            logger.debug(line)

    def join_threads(self) -> None:
        for thread in self.threads:
            logger.debug(f"Joining conversion threads: {thread.getName()}")
            thread.join()

    def kill_processes(self) -> None:
        logger.debug("Cleaning up processes")
        for process in self.processes_to_kill:
            logger.debug(f"Killing {process.pid=}")
            process.kill()
