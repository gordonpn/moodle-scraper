from requests import session
from bs4 import BeautifulSoup
import os, sys, itertools, re
import urllib
import configparser
import datetime
import logging
import requests
from lxml import html

moodle_url = "https://moodle.concordia.ca/moodle/"


def get_session():
    session_requests = requests.session()
    login_url = moodle_url + "login/index.php"
    result = session_requests.get(login_url)

    tree = html.fromstring(result.text)
    authenticity_token = list(set(tree.xpath("//input[@name='logintoken']/@value")))[0]

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

    url = moodle_url + "my/"
    result = session_requests.get(
        url,
        headers=dict(referer=url)
    )

    soup = BeautifulSoup(result.text, 'html.parser')
    print(soup.title.string)
    return session_requests


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    username = os.environ["MOODLE_USERNAME"]
    password = os.environ["MOODLE_PASSWORD"]
    get_session()
