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
        request = self.connect(self.url, proxies=proxies, timeout=timeout)
        page = request.text
        request.close()

        match_obj = re.search("file\s*:\s*\"(.+?)\"", page, re.DOTALL)
        url = match_obj.group(1)

        match_obj = re.search("duration\s*:\s*\"(\d*?)\"", page, re.DOTALL)
        try:
            duration = int(match_obj.group(1))
        except:
            duration = None

        try:
            title = re.search("<title>(.+?)</title>", page, re.DOTALL).group(1)
        except:
            title = sites.get_random_text()

        self.configs = {"url": url + "&start=", "title": title, "duration": duration}