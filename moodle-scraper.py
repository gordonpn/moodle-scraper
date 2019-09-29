import logging
import os
import sys
from configparser import ConfigParser

import requests
from bs4 import BeautifulSoup
from requests import session


def get_config():
    config_parser = ConfigParser()
    config_parser.read('moodle-scraper.conf')
    user = ""
    passwd = ""
    custom_path = ""
    if "MOODLE_USERNAME" in os.environ:
        logger.info("Username found in environment variables")
        user = os.environ["MOODLE_USERNAME"]
    else:
        try:
            user = config_parser.get('moodle-scraper', 'username')
        except Exception as e:
            logger.error("Error with config file format | " + str(e))
        if user != "":
            logger.info("Username found in config file")

    if "MOODLE_PASSWORD" in os.environ:
        logger.info("Password found in environment variables")
        passwd = os.environ["MOODLE_PASSWORD"]
    else:
        try:
            passwd = config_parser.get('moodle-scraper', 'password')
        except Exception as e:
            logger.error("Error with config file format | " + str(e))
        if passwd != "":
            logger.info("Password found in config file")

    if user == "" or passwd == "":
        logger.error("Did not find any authentication data, exiting...")
        sys.exit(-1)

    try:
        custom_path = config_parser.get('moodle-scraper', 'folder')
    except Exception as e:
        logger.error("Error with config file format | " + str(e))
    if custom_path != "":
        logger.info("User defined folder found in config file")
    else:
        custom_path = os.getcwd()
        logger.info("Using default folder ")

    return user, passwd, custom_path


def get_session():
    session_requests = requests.session()
    login_url = moodle_url + "login/index.php"
    try:
        result = session_requests.get(login_url)
    except ConnectionError as e:
        logger.error("Could not connect to Moodle, maybe it's down? " + str(e))
        sys.exit()

    soup = BeautifulSoup(result.text, 'html.parser')
    authenticity_token = soup.find("input", {"name": "logintoken"})['value']

    auth_data = {
        'logintoken': authenticity_token,
        'username': username,
        'password': password
    }

    logger.info("Attempting to authenticate...")
    result = session_requests.post(login_url, data=auth_data, headers=dict(referer=login_url))

    url = moodle_url + "my/"
    result = session_requests.get(url, headers=dict(referer=url))
    soup = BeautifulSoup(result.text, 'html.parser')

    if soup.title.string == "Dashboard":
        logger.info("Authentication successful")
    else:
        logger.info("Authentication unsuccessful, exiting...")
        sys.exit(-1)

    return session_requests


def get_courses():
    courses_dict = {}
    url = moodle_url + "my/"
    result = session.get(url, headers=dict(referer=url))
    soup = BeautifulSoup(result.text, 'html.parser')
    for header in soup.find_all("h4", {"class": "media-heading"}):
        course_name = header.find("a").string.strip()
        course_moodle = header.find("a").get('href')
        courses_dict[course_name] = course_moodle

    for course in courses_dict.copy():
        if "Work Term" in course:
            courses_dict.pop(course)

    if not bool(courses_dict):
        logger.error("Could not find any courses, exiting...")
        sys.exit()
    else:
        logger.info("Found {} courses successfully".format(len(courses_dict)))

    return courses_dict


def get_files():
    files_per_course = {}
    text_per_course = {}
    logger.info("Going through each course Moodle page")
    for course, link in courses.items():
        files_dict = {}
        text_list = []
        logger.info("Course name: {}, link: {}".format(course, link))
        course_page = session.get(link, headers=dict(referer=link))
        soup = BeautifulSoup(course_page.text, 'html.parser')
        for text in soup.find_all("div", {"class": "no-overflow"}):
            for text_block in text.find_all("p"):
                text_list.append(text_block.getText())
        for activity in soup.find_all("div", {"class": "activityinstance"}):
            file_type = activity.find("img")["src"]
            if "icon" not in file_type:
                extension = ""
                if "pdf" in file_type:
                    extension = ".pdf"
                elif "powerpoint" in file_type:
                    extension = ".ppt"
                file_name = activity.find("span", {"class": "instancename"}).text
                file_name = file_name.replace(' File', '').strip() + extension
                logger.info("Found file: {}".format(file_name))
                file_link = activity.find("a").get('href')
                logger.info("With file link: {}".format(file_link))
                files_dict[file_name] = file_link
        if len(text_list) > 0:
            text_list = [text.replace(u'\xa0', u' ') for text in text_list]
            text_list = list(dict.fromkeys(text_list))
            text_per_course[course] = text_list
        files_per_course[course] = files_dict

    return files_per_course, text_per_course


def create_saving_directory():
    path = user_path + "/courses"

    if not os.path.exists(path):
        try:
            os.mkdir(path)
        except OSError:
            logger.error("Creation of the directory {} failed".format(path))
        else:
            logger.info("Successfully created the directory {} ".format(path))
    else:
        logger.info("{} exists and will be used to save files".format(path))

    for course in files.keys():
        course_path = path + "/" + course
        if not os.path.exists(course_path):
            try:
                os.mkdir(course_path)
            except OSError:
                logger.error("Creation of the directory {} failed".format(course_path))
            else:
                logger.info("Successfully created the directory {} ".format(course_path))
        else:
            logger.info("{} exists and will be used to save files".format(course_path))

    return path


def save_text():
    for course, paragraph in paragraphs.items():
        current_path = save_path + "/" + course + "/course-information.txt"
        if os.path.exists(current_path):
            os.remove(current_path)
        with open(current_path, "w+") as write_file:
            paragraph = [text + "\r\n" for text in paragraph]
            write_file.writelines(paragraph)
        logger.info("Wrote info for {} successfully".format(course))


def save_files():
    for course, links in files.items():
        current_path = save_path + "/" + course
        for name, link in links.items():
            request = session.get(link, headers=dict(referer=link))
            try:
                with open(current_path + '/' + name, 'wb') as write_file:
                    write_file.write(request.content)
            except PermissionError as e:
                logger.error("File with same name is open | " + str(e))


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    moodle_url = "https://moodle.concordia.ca/moodle/"
    username, password, user_path = get_config()
    session = get_session()
    courses = get_courses()
    files, paragraphs = get_files()
    save_path = create_saving_directory()
    save_text()
    save_files()
