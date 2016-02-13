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
LIMIT_ELEMENT = '//ul[contains(@class, "summaryRow")]//var[@class="limit"]/text()'
SCRIPT_DIR = os.path.expanduser('~/.telekom')
SESSION_FILE = os.path.join(SCRIPT_DIR, 'session.pickle')


def make_session(login, password):
    """Log in and store the pickled requests session in file."""
    session = requests.Session()
    session.post(LOGIN_URL, data={"service": "TF-pwd", "logonId": login, "password": password})
    with open(SESSION_FILE, 'wb') as f:
        pickle.dump(session, f)


def download_page():
    """Restore the session from the pickled file and download the balance page."""
    with open(SESSION_FILE, 'rb') as f:
        session = pickle.load(f)
    return session.get(BALANCE_URL).content


def get_limit_from_page(html):
    """Find the var element in the downloaded page which contains the limit in bytes."""
    root = etree.HTML(html)
    # There are multiple <var class="limit"> elements, we are interested in the summary only
    size_in_bytes = root.xpath(LIMIT_ELEMENT)[0]
    return size_in_bytes


def get_balance():
    html = download_page()
    size_in_bytes = get_limit_from_page(html)
    human_readable = humanize.naturalsize(int(size_in_bytes), binary=True)
    return "Balance: {} ({})".format(size_in_bytes, human_readable)


def get_platypus_balance():
    """Makes OS X notification if wrapped with Platypus.
    See: http://www.sveinbjorn.org/files/manpages/PlatypusDocumentation.html#10-2
    """
    return 'NOTIFICATION:' + get_balance()


@click.group()
def telekom():
    """Command line application for interacting with the http://www.telekom.hu website."""


@telekom.command()
@click.argument('login', envvar='TELEKOM_LOGIN')
@click.argument('password', envvar='TELEKOM_PASSWORD')
def login(login, password):
    """Login to telekom.hu with TELEKOM_LOGIN and TELEKOM_PASSWORD shell environment variables."""
    try:
        make_session(login, password)
    except IOError:
        os.mkdir(SCRIPT_DIR)
        make_session(login, password)
    else:
        click.echo("Success!")


@telekom.command()
@click.option('--platypus', is_flag=True)
def limit(platypus=False):
    """Shows mobile data limit balance left in human readable form and bytes."""
    click.echo(get_platypus_balance() if platypus else get_balance())


if __name__ == '__main__':
    telekom()
