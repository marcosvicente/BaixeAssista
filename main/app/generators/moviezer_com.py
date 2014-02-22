# coding: utf-8
import re

from ._sitebase import SiteBase
from main.app.util import sites


class Moviezer(SiteBase):
    controller = {
        "url": "http://moviezer.com/video/%s",
        "patterns": (
            re.compile("(?P<inner_url>(?:http://)?moviezer\.com/video/(?P<id>\w+))"),
            [re.compile("(?P<inner_url>(?:http://)?moviezer\.com/e/(?P<id>\w+))")]  #embed url
        ),
        "control": "SM_SEEK",
        "video_control": None
    }

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "moviezer.com"
        self.url = url

    def suportaSeekBar(self):
        return True

    def start_extraction(self, proxies={}, timeout=25):
        fd = self.connect(self.url, proxies=proxies, timeout=timeout)
        web_page = fd.read()
        fd.close()

        matchobj = re.search("flashvars\s*=\s*\{.*?'file':\s*'(?P<url>.*?)'", web_page, re.DOTALL)
        url = matchobj.group("url")

        try:
            title = re.search("<title>(?P<title>.*?)</title>", web_page).group("title")
        except:
            title = sites.get_random_text()

        self.configs = {"url": url + "?start=", "title": title}
