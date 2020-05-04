import logging
import os
import subprocess
from os import path
from subprocess import PIPE, STDOUT, Popen
from threading import Thread
from typing import List

logger = logging.getLogger("moodle_scraper")


class PDFConverter:
    def __init__(self, directory: str):
        self.directory = directory
        self.processes_to_kill: List[Popen] = []
        self.threads: List[Thread] = []

    def run(self) -> None:
        self.convert_to_pdf()
        self.join_threads()
        self.kill_processes()

    def convert_to_pdf(self) -> None:
        path_: str = self.directory
        extensions: List[str] = [".ppt", ".docx", ".xls"]

        if not path_:
            logger.debug(
                "Saving directory not specified, using current working directory"
            )
            path_ = f"{os.getcwd()}/courses"
            logger.debug(path_)

        for root, dirs, files in os.walk(path_):
            for file_ in files:
                if file_.endswith(tuple(extensions)):
                    logger.debug(f"Found {file_}")
                    filename: str = f"{file_[: file_.rfind('.')]}.pdf"
                    if path.exists(f"{root}/{filename}"):
                        logger.debug(f"{filename} already exists, skipping conversion")
                    else:
                        logger.debug(f"{filename} does not exist, will convert.")
                        t = Thread(
                            target=self._conversion_job,
                            kwargs={"file_to_convert": file_, "root": root},
                        )
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
