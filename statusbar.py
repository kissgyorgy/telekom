# -*- coding: utf-8 -*-
from __future__ import absolute_import

import rumps
import telekom


class AwesomeStatusBarApp(rumps.App):
    @rumps.clicked("Preferences")
    def prefs(self, _):
        rumps.alert("jk! no preferences available!")

    @rumps.clicked("Silly button")
    def onoff(self, sender):
        sender.state = not sender.state

    @rumps.clicked("Say hi")
    def sayhi(self, _):
        rumps.notification("Awesome title", "amazing subtitle", "hi!!1")

    @rumps.clicked("Telekom")
    def get_limit(self, _):
        session = telekom.load_session()
        page_content = session.get(telekom.BALANCE_URL).content
        hr, sib = telekom.get_limit(page_content)
        rumps.alert('Balance: {} ({})'.format(hr, sib))


if __name__ == "__main__":
    AwesomeStatusBarApp("Awesome App").run()
