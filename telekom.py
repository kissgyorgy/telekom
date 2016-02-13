#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import pickle
import click
import requests
import humanize
from lxml import etree


LOGIN_URL = "https://www.telekom.hu/login/UI/Login"
BALANCE_URL = "https://www.telekom.hu/shop/tmws/CCServiceDisplayCmd?storeId=2001&langId=-11&postpCode=HFFUP&returnURL=WSMonthlyTrafficCmd"
# There are multiple <var class="limit"> elements, we are interested in the summary only
LIMIT_ELEMENT = '//ul[contains(@class, "summaryRow")]//var[@class="limit"]/text()'
SCRIPT_DIR = os.path.expanduser('~/.telekom')
SESSION_FILE = os.path.join(SCRIPT_DIR, 'session.pickle')


@click.group()
def telekom():
    pass


@telekom.command(name='login')
@click.argument('login', envvar='TELEKOM_LOGIN')
@click.argument('password', envvar='TELEKOM_PASSWORD')
def make_session(login, password):
    """Login to telekom.hu with TELEKOM_LOGIN and TELEKOM_PASSWORD shell environment variables."""
    sess = requests.Session()
    sess.post(LOGIN_URL, data={"service": "TF-pwd", "logonId": login, "password": password})
    try:
        save_session(sess)
    except IOError:
        os.mkdir(SCRIPT_DIR)
        save_session(sess)
    click.echo("Success!")


def save_session(session):
    with open(SESSION_FILE, 'wb') as f:
        pickle.dump(session, f)


def load_session():
    with open(SESSION_FILE, 'rb') as f:
        return pickle.load(f)


def get_limit(page_content):
    root = etree.HTML(page_content)
    size_in_bytes = root.xpath(LIMIT_ELEMENT)[0]
    human_readable = humanize.naturalsize(int(size_in_bytes), binary=True)
    return human_readable, size_in_bytes


@telekom.command(name="limit")
def print_limit():
    """Shows mobile data limit balance left in human readable form and bytes."""
    session = load_session()
    page_content = session.get(BALANCE_URL).content
    hr, sib = get_limit(page_content)
    click.echo("Balance: {} ({})".format(hr, sib))


if __name__ == '__main__':
    telekom()
