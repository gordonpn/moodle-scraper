import logging
import os
import subprocess
import sys
import threading
import time
from subprocess import STDOUT, PIPE
from configparser import ConfigParser
from typing import Dict, List, Tuple

import requests
from bs4 import BeautifulSoup
from requests import session
from requests.adapters import HTTPAdapter


def get_config() -> Tuple[str, str, str, List[str]]:
    config_parser: ConfigParser = ConfigParser()
    config_parser.read('moodle-scraper.conf')

    try:
        user: str = _get_username(config_parser)
        passwd: str = _get_password(config_parser)
        custom_path: str = _get_save_folder(config_parser)
        exclusions: List[str] = _get_exclusions(config_parser)

    except Exception as e:
        logger.error(f"Error with config file format | {str(e)}")
        sys.exit(-1)

    return user, passwd, custom_path, exclusions


def _get_exclusions(config_parser: ConfigParser) -> List[str]:
    exclusions: List[str] = []
    if config_parser.has_option('moodle-scraper', 'exclusions'):
        exclusions_text = config_parser.get('moodle-scraper', 'exclusions')
        if not exclusions_text:
            logger.info("No user defined course exclusions found in config file")
        else:
            exclusions = exclusions_text.lower().split(',')
            exclusions = [text.strip() for text in exclusions]
            logger.info("User defined course exclusions found in config file:")
            for text in exclusions:
                logger.info(f"{text}")
    return exclusions


def _get_save_folder(config_parser: ConfigParser) -> str:
    custom_path: str = ""
    if config_parser.has_option('moodle-scraper', 'folder'):
        custom_path: str = config_parser.get('moodle-scraper', 'folder')
    if not custom_path:
        custom_path = os.getcwd()
        logger.info("Using default folder ")
    else:
        logger.info("User defined folder found in config file")
    return custom_path


def _get_password(config_parser: ConfigParser) -> str:
    passwd: str = ""
    if "MOODLE_PASSWORD" in os.environ:
        logger.info("Password found in environment variables")
        passwd: str = os.environ["MOODLE_PASSWORD"]
    else:
        if config_parser.has_option('moodle-scraper', 'password'):
            passwd = config_parser.get('moodle-scraper', 'password')
        if not passwd:
            logger.error("Password not found in config file")
            sys.exit(-1)
        else:
            logger.info("Password found in config file")
    return passwd


def _get_username(config_parser: ConfigParser) -> str:
    user: str = ""
    if "MOODLE_USERNAME" in os.environ:
        logger.info("Username found in environment variables")
        user: str = os.environ["MOODLE_USERNAME"]
    else:
        if config_parser.has_option('moodle-scraper', 'username'):
            user = config_parser.get('moodle-scraper', 'username')
        if not user:
            logger.error("Username not found in config file")
            sys.exit(-1)
        else:
            logger.info("Username found in config file")
    return user


def get_session() -> session():
    session_requests = requests.session()
    login_url: str = moodle_url + "login/index.php"
    try:
        result = session_requests.get(login_url)
    except Exception as e:
        logger.error(f"Could not connect to Moodle, it could be down | {str(e)}")
        sys.exit()

    soup = BeautifulSoup(result.text, 'html.parser')
    authenticity_token = soup.find("input", {"name": "logintoken"})['value']

    auth_data: Dict[str, str] = {
        'logintoken': authenticity_token,
        'username': username,
        'password': password
    }

    logger.info("Attempting to authenticate...")
    result = session_requests.post(login_url, data=auth_data, headers=dict(referer=login_url))
    logger.info(f"Status code: {result.status_code}")

    url: str = moodle_url + "my/"
    result = session_requests.get(url, headers=dict(referer=url))
    soup = BeautifulSoup(result.text, 'html.parser')

    if soup.title.string == "Dashboard":
        logger.info("Authentication successful")
    else:
        logger.info("Authentication unsuccessful, exiting...")
        sys.exit(-1)

    return session_requests


def get_courses() -> Dict[str, str]:
    courses_dict: Dict[str, str] = {}
    url: str = moodle_url + "my/"
    result = session.get(url, headers=dict(referer=url))
    soup = BeautifulSoup(result.text, 'html.parser')
    for header in soup.find_all("h4", {"class": "media-heading"}):
        course_name: str = header.find("a").string.strip()
        course_moodle: str = header.find("a").get('href')
        courses_dict[course_name] = course_moodle

    if excluded_courses:
        for course in courses_dict.copy():
            for exclusion in excluded_courses:
                if exclusion in course.lower():
                    courses_dict.pop(course)

    if not bool(courses_dict):
        logger.error("Could not find any courses, exiting...")
        sys.exit()
    else:
        logger.info(f"Found {len(courses_dict)} courses successfully:")
        for course in courses_dict.keys():
            logger.info(course)

    return courses_dict


def get_files() -> Tuple[Dict[str, Dict[str, str]], Dict[str, List[str]], int]:
    num_of_files: int = 0
    files_per_course: Dict[str, Dict[str, str]] = {}
    text_per_course: Dict[str, List[str]] = {}
    logger.info("Going through each course Moodle page")
    for course, link in courses.items():
        logger.info(f"Course name: {course}, link: {link}")
        course_page = session.get(link, headers=dict(referer=link))
        soup = BeautifulSoup(course_page.text, 'html.parser')

        text_list: List[str] = []
        for text in soup.find_all("div", {"class": "no-overflow"}):
            for text_block in text.find_all("p"):
                text_list.append(text_block.getText())

        if len(text_list) > 0:
            text_list = [text.replace(u'\xa0', u' ') for text in text_list]
            text_list = list(dict.fromkeys(text_list))
            text_per_course[course] = text_list

        files_dict: Dict[str, str] = _get_files_dict(soup)
        num_of_files = num_of_files + len(files_dict)
        files_per_course[course] = files_dict

    logger.debug(f"Size of pool: {num_of_files}")
    return files_per_course, text_per_course, num_of_files


def _get_files_dict(soup) -> Dict[str, str]:
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
            file_name = activity.find("span", {"class": "instancename"}).text
            file_name = file_name.replace(' File', '').strip() + extension
            logger.info(f"Found file: {file_name}")
            file_link = activity.find("a").get('href')
            logger.info(f"With file link: {file_link}")
            files_dict[file_name] = file_link

    return files_dict


def create_saving_directory() -> Tuple[str, List[str]]:
    path: str = user_path + "/courses"
    course_paths: List[str] = []

    if not os.path.exists(path):
        try:
            os.mkdir(path)
        except OSError:
            logger.error(f"Creation of the directory {path} failed")
        else:
            logger.info(f"Successfully created the directory {path} ")
    else:
        logger.info(f"{path} exists and will be used to save files")

    for course in files.keys():
        course_path = path + "/" + course
        course_paths.append(course_path)
        if not os.path.exists(course_path):
            try:
                os.mkdir(course_path)
            except OSError:
                logger.error(f"Creation of the directory {course_path} failed")
            else:
                logger.info(f"Successfully created the directory {course_path}")
        else:
            logger.info(f"{course_path} exists and will be used to save files")

    return path, course_paths


def save_text() -> None:
    for course, paragraph in paragraphs.items():
        current_path: str = save_path + "/" + course + "/course-information.txt"
        if os.path.exists(current_path):
            os.remove(current_path)
        with open(current_path, "w+") as write_file:
            paragraph: List[str] = [text + "\r\n" for text in paragraph]
            write_file.writelines(paragraph)
        logger.info(f"Wrote info for {course} successfully")


def save_files() -> None:
    for course, links in files.items():
        current_path: str = save_path + "/" + course
        for name, link in links.items():
            t = threading.Thread(target=_parallel_save_files,
                                 kwargs={'current_path': current_path, 'name': name, 'link': link})
            threads_list.append(t)
            t.start()


def _parallel_save_files(current_path=None, name=None, link=None) -> None:
    params_are_valid: bool = current_path and name and link

    if params_are_valid:
        logger.info(f"Attempting parallel download of {name}")
        try:
            request = session.get(link, headers=dict(referer=link))
            with open(current_path + '/' + name, 'wb') as write_file:
                write_file.write(request.content)
        except Exception as e:
            logger.error(f"File with same name is open | {str(e)}")
    else:
        logger.error("Some parameters were missing for parallel downloads")


def clean_up_threads() -> None:
    for thread in threads_list:
        logger.debug(f"Joining downloading threads: {thread.getName()}")
        thread.join()


def convert_to_pdf() -> None:
    for course_path in course_paths_list:
        for file_ in os.listdir(course_path):
            if file_.endswith('.ppt'):
                process = subprocess.Popen(["libreoffice", "--headless", "--convert-to", "pdf", file_],
                                           cwd=course_path + "/",
                                           stdout=PIPE,
                                           stderr=STDOUT)
                for line in process.stdout:
                    logger.debug(line)
                files_to_remove.append(course_path + "/" + file_)


def clean_duplicates():
    time.sleep(60)
    for file_ in files_to_remove:
        os.remove(file_)


if __name__ == '__main__':
    threads_list: List[threading.Thread] = []
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    moodle_url = "https://moodle.concordia.ca/moodle/"
    username, password, user_path, excluded_courses = get_config()
    session = get_session()
    courses: Dict[str, str] = get_courses()
    files, paragraphs, pool_size = get_files()
    session.mount('https://', HTTPAdapter(pool_connections=pool_size, pool_maxsize=pool_size))
    save_path, course_paths_list = create_saving_directory()
    save_text()
    save_files()
    clean_up_threads()
    files_to_remove: List[str] = []
    convert_to_pdf()
    clean_duplicates()
