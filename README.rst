Command line application for interacting with the http://www.telekom.hu website.


Currently it can login to the website, get the mobile data usage limit, or connect to the internet
with an Alcatel 4G LTE USB stick:

.. code-block:: bash

    Usage: telekom.py [OPTIONS] COMMAND [ARGS]...

      Command line application for interacting with the http://www.telekom.hu
      website.

    Options:
      --help  Show this message and exit.

    Commands:
      connect  Connect to the internet with the Alcatel 4G...
      limit    Shows mobile data limit balance left in human...
      login    Login to telekom.hu with TELEKOM_LOGIN and...


If you wrap it with `Platypus <http://www.sveinbjorn.org/platypus>`_ and call limit command with
the ``--platypus`` option, it will show a notification on OS X.

.. image:: notification.png
