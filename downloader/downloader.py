import logging
import os
import pathlib
import sys
import threading
from typing import Dict, List

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter

from configuration.config import Config

logger = logging.getLogger("moodle_scraper")


class Downloader:
    def __init__(self, username, password, directory):
        self.username = os.getenv("MOODLE_USERNAME", username)
        self.password = os.getenv("MOODLE_PASSWORD", password)
        self.directory = directory
        self.config: Config = Config()
        self.threads_list: List[threading.Thread] = []
        self.moodle_url: str = "https://moodle.concordia.ca/moodle/"
        self.session = None
        self.courses: Dict[str, str] = {}
        self.files: Dict[str, Dict[str, str]] = {}
        self.paragraphs: Dict[str, List[str]] = {}
        self.pool_size: int = 0
        self.save_path: str = ""
        self.course_paths_list: List[str] = []

    def run(self):
        self.config.get_config()
        self.session = self.get_session()
        self.courses = self.get_courses()
        self.get_files()
        self.session.mount(
            "https://",
            HTTPAdapter(pool_connections=self.pool_size, pool_maxsize=self.pool_size),
        )
        self.create_saving_directory()
        self.save_text()
        self.save_files()
        self.clean_up_threads()

    def get_session(self) -> requests.Session:
        if not (self.username and self.password):
            raise ValueError(
                "Username and password must be specified in environment variables or passed as arguments on the "
                "command line "
            )

        session_requests = requests.session()
        login_url: str = f"{self.moodle_url}login/index.php"
        try:
            result = session_requests.get(login_url)
        except Exception as e:
            logger.error(f"Could not connect to Moodle, it could be down | {str(e)}")
            raise ConnectionError

        soup = BeautifulSoup(result.text, "html.parser")
        authenticity_token = soup.find("input", {"name": "logintoken"})["value"]

        auth_data: Dict[str, str] = {
            "logintoken": authenticity_token,
            "username": self.username,
            "password": self.password,
        }

        logger.info("Attempting to authenticate...")
        result = session_requests.post(
            login_url, data=auth_data, headers=dict(referer=login_url)
        )
        logger.info(f"Status code: {result.status_code}")

        url: str = f"{self.moodle_url}my/"
        result = session_requests.get(url, headers=dict(referer=url))
        soup = BeautifulSoup(result.text, "html.parser")

        if soup.title.string == "Dashboard":
            logger.info("Authentication successful")
        else:
            logger.info("Authentication unsuccessful, exiting...")
            raise ConnectionRefusedError

        return session_requests

    def get_courses(self) -> Dict[str, str]:
        courses_dict: Dict[str, str] = {}
        url: str = f"{self.moodle_url}my/"
        result = self.session.get(url, headers=dict(referer=url))
        soup = BeautifulSoup(result.text, "html.parser")
        for header in soup.find_all("h4", {"class": "media-heading"}):
            course_name: str = header.find("a").string.strip()
            course_moodle: str = header.find("a").get("href")
            courses_dict[course_name] = course_moodle

        if self.config.excluded_courses:
            for course in courses_dict.copy():
                for exclusion in self.config.excluded_courses:
                    if exclusion in course.lower():
                        courses_dict.pop(course)

        if not bool(courses_dict):
            logger.error("Could not find any courses, exiting...")
            sys.exit(0)
        else:
            logger.info(f"Found {len(courses_dict)} courses successfully:")
            for course in courses_dict:
                logger.info(course)

        return courses_dict

    def get_files(self) -> None:
        num_of_files: int = 0
        files_per_course: Dict[str, Dict[str, str]] = {}
        text_per_course: Dict[str, List[str]] = {}
        logger.info("Going through each course Moodle page")
        for course, link in self.courses.items():
            logger.info(f"Course name: {course}, link: {link}")
            course_page = self.session.get(link, headers=dict(referer=link))
            soup = BeautifulSoup(course_page.text, "html.parser")

            text_list: List[str] = []
            for text in soup.find_all("div", {"class": "no-overflow"}):
                for text_block in text.find_all("p"):
                    text_list.append(text_block.getText())

            if text_list:
                text_list = [text.replace("\xa0", " ") for text in text_list]
                text_list = list(dict.fromkeys(text_list))
                text_per_course[course] = text_list

            files_dict: Dict[str, str] = self._get_files_dict(soup)
            num_of_files += len(files_dict)
            files_per_course[course] = files_dict

        logger.debug(f"Size of pool: {num_of_files}")
        self.files = files_per_course
        self.paragraphs = text_per_course
        self.pool_size = num_of_files

    def _get_files_dict(self, soup) -> Dict[str, str]:
        files_dict: Dict[str, str] = {}

        for activity in soup.find_all("div", {"class": "activityinstance"}):
            file_type = activity.find("img")["src"]
            if "icon" not in file_type:
                extension = ""
                if "pdf" in file_type:
                    extension = ".pdf"
                elif "powerpoint" in file_type:
                    extension = ".ppt"
                elif "archive" in file_type:
                    extension = ".zip"
                elif "text" in file_type:
                    extension = ".txt"
                elif "spreadsheet" in file_type:
                    extension = ".xls"
                file_name = activity.find("span", {"class": "instancename"}).text
                file_name = file_name.replace(" File", "").strip() + extension
                logger.info(f"Found file: {file_name}")
                file_link = activity.find("a").get("href")
                logger.info(f"With file link: {file_link}")
                files_dict[file_name] = file_link

        return files_dict

    def create_saving_directory(self) -> None:
        path: str = self.directory

        if not self.directory:
            logger.debug(
                "Saving directory not specified, using current working directory"
            )
            path = f"{os.getcwd()}/courses"
            logger.debug(path)

        course_paths: List[str] = []

        if not os.path.exists(path):
            try:
                pathlib.Path(path).mkdir(parents=True, exist_ok=True)
            except OSError:
                logger.error(f"Creation of the directory {path} failed")
                raise OSError
            else:
                logger.info(f"Successfully created the directory {path} ")
        else:
            logger.info(f"{path} exists and will be used to save files")

        for course in self.files.keys():
            course_path = f"{path}/{course}"
            course_paths.append(course_path)
            if not os.path.exists(course_path):
                try:
                    os.mkdir(course_path)
                except OSError:
                    logger.error(f"Creation of the directory {course_path} failed")
                    raise OSError
                else:
                    logger.info(f"Successfully created the directory {course_path}")
            else:
                logger.info(f"{course_path} exists and will be used to save files")

        self.save_path = path
        self.course_paths_list = course_paths

    def save_text(self) -> None:
        for course, paragraph in self.paragraphs.items():
            current_path: str = f"{self.save_path}/{course}/course-information.txt"
            if os.path.exists(current_path):
                os.remove(current_path)
            with open(current_path, "w+") as write_file:
                paragraph_text: List[str] = [f"{text}\r\n" for text in paragraph]
                write_file.writelines(paragraph_text)
            logger.info(f"Wrote info for {course} successfully")

    def save_files(self) -> None:
        for course, links in self.files.items():
            current_path: str = f"{self.save_path}/{course}"
            for name, link in links.items():
                t = threading.Thread(
                    target=self._parallel_save_files,
                    kwargs={"current_path": current_path, "name": name, "link": link},
                )
                self.threads_list.append(t)
                t.start()

    def _parallel_save_files(self, current_path=None, name=None, link=None) -> None:
        params_are_valid: bool = current_path and name and link

        if params_are_valid:
            logger.info(f"Attempting parallel download of {name}")
            try:
                request = self.session.get(link, headers=dict(referer=link))
                with open(f"{current_path}/{name}", "wb") as write_file:
                    write_file.write(request.content)
            except Exception as e:
                logger.error(f"File with same name is open | {str(e)}")
        else:
            logger.error("Some parameters were missing for parallel downloads")

    def clean_up_threads(self) -> None:
        for thread in self.threads_list:
            logger.debug(f"Joining downloading threads: {thread.getName()}")
            thread.join()
