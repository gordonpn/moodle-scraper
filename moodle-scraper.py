from requests import session
from bs4 import BeautifulSoup
import os, sys, itertools, re
import urllib
import configparser
import datetime
import logging
import requests


def get_config():
    # if none set, exit
    user = ""
    passwd = ""
    if "MOODLE_USERNAME" in os.environ:
        logger.info("Username found in env variables")
        user = os.environ["MOODLE_USERNAME"]
    else:
        user = ""
        # get from config file
    if "MOODLE_PASSWORD" in os.environ:
        logger.info("Password found in env variables")
        passwd = os.environ["MOODLE_PASSWORD"]
    else:
        passwd = ""

    return user, passwd


def get_session():
    session_requests = requests.session()
    login_url = moodle_url + "login/index.php"
    result = session_requests.get(login_url)

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

    if (soup.title.string == "Dashboard"):
        logger.info("Authentication successful")
    else:
        logger.info("Authentication unsuccessful")
        logger.info("Exiting...")
        exit(-1)

    return session_requests


def get_courses():
    courses_dict = {}
    url = moodle_url + "my/"
    result = session.get(url, headers=dict(referer=url))
    soup = BeautifulSoup(result.text, 'html.parser')
    for header in soup.find_all("h4", {"class": "media-heading"}):
        courses_dict[header.find("a").string] = header.find("a").get('href')

    for course in courses_dict.copy():
        if "Work Term" in course:
            courses_dict.pop(course)

    if (bool(courses_dict) == False):
        logger.error("Could not find any courses")
        logger.info("Exiting...")
        exit(-1)
    else:
        logger.info("Found {} courses successfully".format(len(courses_dict)))

    return courses_dict


def get_files():
    files_per_course = {}
    files_list = []
    for course, link in courses:
        course_page = session.get(link, headers=dict(referer=link))
        soup = BeautifulSoup(course_page.text, 'html.parser')
        print(soup.find_all("div", {"class": "activityinstance"}))

    return files_list


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    moodle_url = "https://moodle.concordia.ca/moodle/"
    username, password = get_config()
    session = get_session()
    courses = get_courses()
    files = get_files()
