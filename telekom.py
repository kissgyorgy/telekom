#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import time
import pickle
import subprocess
import click
import requests
import humanize


LOGIN_URL = "https://www.telekom.hu/login/UI/Login"
BALANCE_URL = "https://www.telekom.hu/shop/tmws/CCServiceDisplayCmd?storeId=2001&langId=-11&postpCode=HFFUP&returnURL=WSMonthlyTrafficCmd"  # noqa
# utf-8 encoded str
SESSION_EXPIRED_MESSAGE = 'BELÉPÉS A SZOLGÁLTATÁS MEGRENDELÉSÉHEZ'
LIMIT_ELEMENT = '//ul[contains(@class, "summaryRow")]//var[@class="limit"]/text()'
SCRIPT_DIR = os.path.expanduser('~/.telekom')
SESSION_FILE = os.path.join(SCRIPT_DIR, 'session.pickle')
# IP address is always available, w800.home sometimes not
STICK_URL = 'http://192.168.0.1'
# default value?
PROFILE_ID = 16
WEB_CONNECTION_APP = '/Volumes/Web Connection/Web Connection.app'


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


def is_connection_ok():
    try:
        return requests.get(STICK_URL).ok
    except requests.ConnectionError:
        return False


def wait_for_web_connection_mount():
    while True:
        try:
            subprocess.check_output(['open', '-a', WEB_CONNECTION_APP], stderr=subprocess.STDOUT)
            click.echo()
            break
        except subprocess.CalledProcessError:
            click.echo('.', nl=False)
            time.sleep(1)


def wait_for_boot():
    while not is_connection_ok():
        click.echo('.', nl=False)
        time.sleep(1)

    click.echo()


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


@telekom.command()
@click.argument('username', envvar='TELEKOM_STICK_USERNAME')
@click.argument('password', envvar='TELEKOM_STICK_PASSWORD')
@click.argument('pin', envvar='TELEKOM_STICK_PIN')
def connect(username, password, pin):
    """Connect to the internet with the Alcatel 4G LTE modem."""
    click.echo('Checking connection...')
    if not is_connection_ok():
        click.echo('Waiting for Web Connection app...')
        wait_for_web_connection_mount()
        click.echo('Waiting for stick to boot...')
        wait_for_boot()

    click.echo('Logging in...')
    requests.post(STICK_URL + '/goform/setLogin', {'username': username, 'password': password})
    click.echo('Setting PIN...')
    requests.post(STICK_URL + '/goform/unlockPIN', {'pin': pin})
    click.echo('Connecting...')
    requests.post(STICK_URL + '/goform/setWanConnect', {'profile_id': PROFILE_ID})
    click.echo('Logging out...')
    requests.post(STICK_URL + '/goform/setLogout')
    click.echo('Done.')


@telekom.command()
@click.argument('state', type=click.Choice(['on', 'off']))
def wifi(state='on'):
    click.echo('Turning wifi ' + state)


if __name__ == '__main__':
    telekom()
