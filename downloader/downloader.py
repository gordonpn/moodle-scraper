import concurrent.futures
import logging
import os
import pathlib
import re
import sys
from os import path
from random import randint
from threading import Thread
from time import sleep
from typing import Dict, List

import requests
import urllib3
from bs4 import BeautifulSoup
from configuration.config import Config
from jinja2 import Environment, FileSystemLoader
from notifier.notifier import Notifier
from requests.adapters import HTTPAdapter
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger("moodle_scraper")


class Downloader:
    def __init__(self, username, password, directory):
        self.username = os.getenv("MOODLE_USERNAME", username)
        self.password = os.getenv("MOODLE_PASSWORD", password)
        self.directory = directory
        self.config: Config = Config()
        self.threads_list: List[Thread] = []
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

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_prefs = {"profile.default_content_settings": {"images": 2}}
        chrome_options.experimental_options["prefs"] = chrome_prefs

        driver = webdriver.Chrome(chrome_options=chrome_options)
        driver.get(f"{self.moodle_url}login/index.php")
        wait = WebDriverWait(driver, 10)
        log_in_button = wait.until(
            expected_conditions.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "#region-main > div > div.row.justify-content-center > div > div > div > div > div > div:nth-child(2) > div.potentialidplist.mt-3 > div > a",
                )
            )
        )
        driver.execute_script("arguments[0].click();", log_in_button)
        driver.find_element_by_css_selector("#userNameInput").send_keys(self.username)
        driver.find_element_by_css_selector("#passwordInput").send_keys(self.password)
        driver.execute_script(
            "arguments[0].click();",
            driver.find_element_by_css_selector("#submitButton"),
        )

        session_requests = requests.session()
        cookies = driver.get_cookies()
        for cookie in cookies:
            session_requests.cookies.set(cookie["name"], cookie["value"])

        driver.close()

        return session_requests

    def get_courses(self) -> Dict[str, str]:
        courses_dict: Dict[str, str] = {}
        url: str = f"{self.moodle_url}"
        result = self.session.get(url, headers=dict(referer=url), verify=False)
        soup = BeautifulSoup(result.text, "html.parser")
        course_sidebar = soup.select("#nav-drawer > nav > ul")

        for header in course_sidebar[0].find_all("li"):
            header_link = header.find("a")
            if header_link:
                course_name = header_link.select("div > div > span.media-body")[
                    0
                ].get_text(strip=True)

                if re.search(r"[A-Z]{4}-[\d]{3}.*", course_name):
                    course_link = header_link.get("href")
                    courses_dict[course_name] = course_link

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
            course_page = self.session.get(
                link, headers=dict(referer=link), verify=False
            )
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
            extension = self._get_extension(file_type)
            if extension is None:
                continue

            file_name = activity.find("span", {"class": "instancename"}).text
            file_name = file_name.replace(" File", "").strip() + extension
            logger.info(f"Found file: {file_name}")
            file_link = activity.find("a").get("href")
            logger.info(f"With file link: {file_link}")
            files_dict[file_name] = file_link

        for file_in_sub_folder in soup.find_all("span", {"class": "fp-filename-icon"}):
            file_link = file_in_sub_folder.find("a").get("href")
            file_name = file_in_sub_folder.find("span", {"class": "fp-filename"}).text
            logger.info(f"Found file: {file_name}")
            logger.info(f"With file link: {file_link}")
            files_dict[file_name] = file_link

        return files_dict

    def _get_extension(self, file_type):
        if "icon" not in file_type:
            if "mpeg" in file_type:
                return None
            elif "pdf" in file_type:
                return ".pdf"
            elif "powerpoint" in file_type:
                return ".pptx"
            elif "archive" in file_type:
                return ".zip"
            elif "text" in file_type:
                return ".txt"
            elif "spreadsheet" in file_type:
                return ".xlsx"
            elif "document" in file_type:
                return ".docx"
        else:
            if "quiz" in file_type or "assign" in file_type:
                return ".html"

    def _get_nested_files(self):
        pass

    def create_saving_directory(self) -> None:
        this_path: str = self.directory

        if not self.directory:
            logger.debug(
                "Saving directory not specified, using current working directory"
            )
            this_path = f"{os.getcwd()}/courses"
            logger.debug(this_path)

        course_paths: List[str] = []

        if not os.path.exists(this_path):
            try:
                pathlib.Path(this_path).mkdir(parents=True, exist_ok=True)
            except OSError as e:
                logger.error(str(e))
                logger.error(f"Creation of the directory {this_path} failed")
                raise OSError
            else:
                logger.info(f"Successfully created the directory {this_path} ")
        else:
            logger.info(f"{this_path} exists and will be used to save files")

        for course in self.files.keys():
            course_path = f"{this_path}/{course}"
            course_paths.append(course_path)
            if not os.path.exists(course_path):
                try:
                    pathlib.Path(course_path).mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    logger.error(str(e))
                    logger.error(f"Creation of the directory {course_path} failed")
                    raise OSError
                else:
                    logger.info(f"Successfully created the directory {course_path}")
            else:
                logger.info(f"{course_path} exists and will be used to save files")

        self.save_path = this_path
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
        notifier = Notifier()
        for course, links in self.files.items():
            current_path: str = f"{self.save_path}/{course}"
            for name, link in links.items():
                name = name.replace("/", "")
                if path.exists(f"{current_path}/{name}"):
                    logging.debug(f"{name} already exists, skipping download")
                else:
                    t = Thread(
                        target=self._parallel_save_files,
                        kwargs={
                            "current_path": current_path,
                            "name": name,
                            "link": link,
                        },
                    )
                    self.threads_list.append(t)
                    t.start()
                    msg: str = f"New file:\n{course}\n{name}"
                    concurrent.futures.ThreadPoolExecutor().submit(notifier.notify, msg)

    def _parallel_save_files(self, current_path=None, name=None, link=None) -> None:
        params_are_valid: bool = current_path and name and link

        if params_are_valid:
            sleep_time = randint(10, 120)
            logger.info(
                f"Waiting {sleep_time} seconds before parallel download of {name}"
            )
            sleep(sleep_time)
            try:
                if ".html" in name:
                    env = Environment(loader=FileSystemLoader("assets"))
                    template = env.get_template("link_template.html")
                    output = template.render(url_name=name, url=link)
                    with open(f"{current_path}/{name}", "w") as write_file:
                        write_file.write(output)
                else:
                    request = self.session.get(
                        link, headers=dict(referer=link), verify=False
                    )
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
