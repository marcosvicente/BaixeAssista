# coding: utf-8
import re

from ._sitebase import SiteBase
from main.app.util import sites


class Supervideo(SiteBase):
    # http://supervideo.biz/embed-duzx1non5fch-518x392.html

    controller = {
        "url": "http://supervideo.biz/%s",
        "patterns": (
            [re.compile("(?P<inner_url>http://supervideo\.biz/(?P<id>.+))")],
        ),
        "control": "SM_RANGE",
        "video_control": None
    }

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "supervideo.biz"
        self.url = url

    def start_extraction(self, proxies={}, timeout=25):
        fd = self.connect(self.url, proxies=proxies, timeout=timeout)
        web_page = fd.read()
        fd.close()

        matchobj = re.search("file\s*:\s*\"(.+?)\"", web_page, re.DOTALL)
        url = matchobj.group(1)

        matchobj = re.search("duration\s*:\s*\"(\d*?)\"", web_page, re.DOTALL)
        try:
            duration = int(matchobj.group(1))
        except:
            duration = None

        try:
            title = re.search("<title>(.+?)</title>", web_page, re.DOTALL).group(1)
        except:
            title = sites.get_random_text()

        self.configs = {"url": url + "&start=", "title": title, "duration": duration}