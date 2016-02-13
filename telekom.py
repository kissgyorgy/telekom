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


def make_session(login, password):
    session = requests.Session()
    session.post(LOGIN_URL, data={"service": "TF-pwd", "logonId": login, "password": password})
    with open(SESSION_FILE, 'wb') as f:
        pickle.dump(session, f)


def download_page():
    with open(SESSION_FILE, 'rb') as f:
        session = pickle.load(f)
    return session.get(BALANCE_URL).content


def get_limit_from_page(html):
    root = etree.HTML(html)
    size_in_bytes = root.xpath(LIMIT_ELEMENT)[0]
    human_readable = humanize.naturalsize(int(size_in_bytes), binary=True)
    return human_readable, size_in_bytes


def get_balance():
    html = download_page()
    hr, sib = get_limit_from_page(html)
    return "Balance: {} ({})".format(hr, sib)


def get_platypus_balance():
    return 'NOTIFICATION:' + get_balance()


@telekom.command(name="limit")
@click.option('--platypus', is_flag=True)
def print_limit(platypus=False):
    """Shows mobile data limit balance left in human readable form and bytes."""
    click.echo(get_platypus_balance() if platypus else get_balance())


if __name__ == '__main__':
    telekom()
