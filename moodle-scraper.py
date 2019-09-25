from requests import session
from bs4 import BeautifulSoup
import os, sys, itertools, re
import urllib
import configparser
import datetime
import logging
import requests

moodle_url = "https://moodle.concordia.ca/moodle/"


def get_config():
    # if none set, exit
    user = ""
    passwd = ""
    if "MOODLE_USERNAME" in os.environ:
        user = os.environ["MOODLE_USERNAME"]
    else:
        user = ""
        # get from config file
    if "MOODLE_PASSWORD" in os.environ:
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

    result = session_requests.post(
        login_url,
        data=auth_data,
        headers=dict(referer=login_url)
    )

    return session_requests


def get_courses():
    courses_dict = {}
    url = moodle_url + "my/"
    result = session.get(
        url,
        headers=dict(referer=url)
    )
    soup = BeautifulSoup(result.text, 'html.parser')
    for header in soup.find_all("h4", {"class": "media-heading"}):
        courses_dict[header.find("a").string] = header.find("a").get('href')

    return courses_dict


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    username, password = get_config()
    session = get_session()
    courses = get_courses()
