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
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger("moodle_scraper")
HTML_EXT = ".html"
HTML_PARSER = "html.parser"


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
        self.wait_time: int = 0

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

    def get_webdriver(self):
        attempts_left: int = 5
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_prefs = {"profile.default_content_settings": {"images": 2}}
        chrome_options.experimental_options["prefs"] = chrome_prefs
        caps = DesiredCapabilities().CHROME
        caps["pageLoadStrategy"] = "eager"

        while attempts_left > 0:
            try:
                driver = webdriver.Chrome(
                    chrome_options=chrome_options, desired_capabilities=caps
                )
            except Exception as e:
                logger.info("Encountered error while creating Selenium driver: %s", e)
                attempts_left -= 1
                continue
            break
        else:
            raise RuntimeError("Could not create Selenium driver after 5 tries")

        return driver

    def get_session(self) -> requests.Session:
        if not (self.username and self.password):
            raise ValueError(
                "Username and password must be specified in "
                "environment variables or passed as arguments on the "
                "command line "
            )

        driver = self.get_webdriver()
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
        username_field = wait.until(
            expected_conditions.presence_of_element_located(
                (By.CSS_SELECTOR, "#userNameInput")
            )
        )
        username_field.send_keys(self.username)
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
        soup = BeautifulSoup(result.text, HTML_PARSER)
        course_sidebar = soup.select("#nav-drawer > nav > ul")

        for header in course_sidebar[0].find_all("li"):
            if header_link := header.find("a"):
                course_name = header_link.select("div > div > span.media-body")[
                    0
                ].get_text(strip=True)

                if re.search(r"[A-Z]{4}-[\d]{3}.*", course_name):
                    course_link = header_link.get("href")
                    courses_dict[course_name] = course_link
                    logger.info("Course: %s", course_name)

        self._check_exclusions(courses_dict)

        if not bool(courses_dict):
            logger.error("Could not find any courses, exiting...")
            sys.exit(0)
        else:
            logger.info("Found %s courses successfully", len(courses_dict))

        return courses_dict

    def _check_exclusions(self, courses_dict):
        if self.config.excluded_courses:
            for course in courses_dict.copy():
                for exclusion in self.config.excluded_courses:
                    if exclusion in course.lower():
                        logger.info("Excluding course: %s", exclusion)
                        courses_dict.pop(course)

    def get_files(self) -> None:
        num_of_files: int = 0
        files_per_course: Dict[str, Dict[str, str]] = {}
        text_per_course: Dict[str, List[str]] = {}
        logger.info("Going through each course Moodle page")
        for course, link in self.courses.items():
            logger.info("Course: %s, link: %s", course, link)
            course_page = self.session.get(
                link, headers=dict(referer=link), verify=False
            )
            soup = BeautifulSoup(course_page.text, HTML_PARSER)

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

        logger.debug("Size of pool: %s", num_of_files)
        self.files = files_per_course
        self.paragraphs = text_per_course
        self.pool_size = num_of_files

    def _get_files_dict(self, soup) -> Dict[str, str]:
        files_dict: Dict[str, str] = {}

        for activity in soup.find_all("div", {"class": "activityinstance"}):
            file_type = activity.find("img")["src"]
            extension = self._get_extension(file_type)
            if not extension:
                continue

            file_name = activity.find("span", {"class": "instancename"}).text
            file_name = file_name.replace(" File", "").strip() + extension
            file_link = activity.find("a").get("href")
            self._log_file(file_name, file_link)
            files_dict[file_name] = file_link

            if HTML_EXT in extension:
                nested_files_dict = self._get_nested_files(file_link)
                files_dict = {**files_dict, **nested_files_dict}

        for file_in_sub_folder in soup.find_all("span", {"class": "fp-filename-icon"}):
            file_link = file_in_sub_folder.find("a").get("href")
            file_name = file_in_sub_folder.find("span", {"class": "fp-filename"}).text
            self._log_file(file_name, file_link)
            files_dict[file_name] = file_link

        return files_dict

    def _log_file(self, file_name, file_link) -> None:
        logger.info("File name: %s", file_name)
        logger.info("File link: %s", file_link)

    def _get_extension(self, file_type) -> str:
        extension = ""
        if "icon" not in file_type:
            if "pdf" in file_type:
                extension = ".pdf"
            elif "powerpoint" in file_type:
                extension = ".pptx"
            elif "archive" in file_type:
                extension = ".zip"
            elif "text" in file_type:
                extension = ".txt"
            elif "spreadsheet" in file_type:
                extension = ".xlsx"
            elif "document" in file_type:
                extension = ".docx"
        elif "quiz" in file_type or "assign" in file_type:
            extension = HTML_EXT
        return extension

    def _get_nested_files(self, link) -> Dict[str, str]:
        result = self.session.get(link, headers=dict(referer=link), verify=False)
        soup = BeautifulSoup(result.text, HTML_PARSER)
        files_dict = {}
        for nested_file in soup.find_all("div", {"class": "fileuploadsubmission"}):
            a_tag = nested_file.find("a", {"target": "_blank"})
            file_link = a_tag.get("href")
            file_name = a_tag.text
            self._log_file(file_name, file_link)
            files_dict[file_name] = file_link

        return files_dict

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
                logger.error("Creation of the directory %s failed", this_path)
                raise OSError
            else:
                logger.info("Successfully created the directory %s ", this_path)
        else:
            logger.info("%s exists and will be used to save files", this_path)

        for course in self.files:
            course_path = f"{this_path}/{course}"
            course_paths.append(course_path)
            if not os.path.exists(course_path):
                try:
                    pathlib.Path(course_path).mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    logger.error(str(e))
                    logger.error("Creation of the directory %s failed", course_path)
                    raise OSError
                else:
                    logger.info("Successfully created the directory %s", course_path)
            else:
                logger.info("%s exists and will be used to save files", course_path)

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
            logger.info("Wrote info for %s successfully", course)

    def save_files(self) -> None:
        notifier = Notifier()
        for course, links in self.files.items():
            current_path: str = f"{self.save_path}/{course}"
            for name, link in links.items():
                name = name.replace("/", "")
                if path.exists(f"{current_path}/{name}"):
                    logging.debug("Already exists, skipping download: %s", name)
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
            sleep_time = self._get_next_wait_time()
            logger.info("Waiting %s seconds before downloading: %s", sleep_time, name)
            sleep(sleep_time)
            try:
                if HTML_EXT in name:
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
                logger.error("File with same name is open | %s", str(e))
        else:
            logger.error("Some parameters were missing for parallel downloads")

    def clean_up_threads(self) -> None:
        for thread in self.threads_list:
            logger.debug("Joining downloading threads: %s", thread.getName())
            thread.join()

    def _get_next_wait_time(self) -> int:
        wait_time = self.wait_time
        self.wait_time += randint(2, 5)
        return wait_time
