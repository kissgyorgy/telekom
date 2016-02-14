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
# utf-8 encoded str
SESSION_EXPIRED_MESSAGE = 'BELÉPÉS A SZOLGÁLTATÁS MEGRENDELÉSÉHEZ'
LIMIT_ELEMENT = '//ul[contains(@class, "summaryRow")]//var[@class="limit"]/text()'
SCRIPT_DIR = os.path.expanduser('~/.telekom')
SESSION_FILE = os.path.join(SCRIPT_DIR, 'session.pickle')


class NotLoggedInError(Exception):
    """Raised when user is not logged in or the session expired."""
    message = 'Session expired!'


def make_session(login, password):
    """Log in and store the pickled requests session in file."""
    session = requests.Session()
    session.post(LOGIN_URL, data={"service": "TF-pwd", "logonId": login, "password": password})
    if not os.path.isdir(SCRIPT_DIR):
        os.mkdir(SCRIPT_DIR)
    with open(SESSION_FILE, 'wb') as f:
        pickle.dump(session, f)


def load_session():
    """Restore the session from the pickled file."""
    with open(SESSION_FILE, 'rb') as f:
        return pickle.load(f)


def download_page(session):
    """Download the balance page with the given session."""
    res = session.get(BALANCE_URL)
    if SESSION_EXPIRED_MESSAGE in res.content:
        raise NotLoggedInError
    else:
        return res.content


def get_limit_from_page(html):
    """Find the var element in the downloaded page which contains the limit in bytes."""
    root = etree.HTML(html)
    # There are multiple <var class="limit"> elements, we are interested in the summary only
    size_in_bytes = root.xpath(LIMIT_ELEMENT)[0]
    return size_in_bytes


def get_balance():
    session = load_session()
    html = download_page(session)
    size_in_bytes = get_limit_from_page(html)
    human_readable = humanize.naturalsize(int(size_in_bytes), binary=True)
    return "Balance: {} ({})".format(size_in_bytes, human_readable)


def get_message(message, is_platypus=False):
    """Makes OS X notification if wrapped with Platypus.
    See: http://www.sveinbjorn.org/files/manpages/PlatypusDocumentation.html#10-2
    """
    return 'NOTIFICATION:' + message if is_platypus else message


@click.group()
def telekom():
    """Command line application for interacting with the http://www.telekom.hu website."""


@telekom.command()
@click.argument('login', envvar='TELEKOM_LOGIN')
@click.argument('password', envvar='TELEKOM_PASSWORD')
@click.option('--platypus', 'is_platypus', is_flag=True)
def login(login, password, is_platypus):
    """Login to telekom.hu with TELEKOM_LOGIN and TELEKOM_PASSWORD shell environment variables."""
    make_session(login, password)
    click.echo(get_message("Success!", is_platypus))


@telekom.command()
@click.option('--platypus', 'is_platypus', is_flag=True)
def limit(is_platypus=False):
    """Shows mobile data limit balance left in human readable form and bytes."""
    try:
        click.echo(get_message(get_balance(), is_platypus))
    except NotLoggedInError as e:
        click.echo(get_message(e.message, is_platypus))


if __name__ == '__main__':
    telekom()
