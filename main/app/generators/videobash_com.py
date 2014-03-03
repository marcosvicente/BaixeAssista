# coding: utf-8
from ._sitebase import *


class Videobash(SiteBase):
    ##
    # www.videobash.com/embed/NDMwMzU5
    # http://www.videobash.com/video_show/acirc-thriller-acirc-halloween-light-show-6225
    ##
    controller = {
        "url": "http://www.videobash.com/%s",
        "patterns": (
            re.compile("(?P<inner_url>http://www\.videobash\.com/(?P<id>video_show/.+))"),
            [re.compile("(?P<inner_url>http://www\.videobash\.com/(?P<id>embed/.+))")],
        ),
        "control": "SM_RANGE",
        "video_control": None
    }

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "videobash.com"
        self.url = url

    def start_extraction(self, proxies={}, timeout=25):
        request = self.connect(self.url, proxies=proxies, timeout=timeout)
        page = request.text
        request.close()

        match_obj = re.search(
            "flashvars\s*\+=\s*(?:\"|').*?file=(?:\"|')\s*\+?\s*(?:\"|')(?:http://)?(?:\"|')\s*\+?\s*(?:\"|')(.+?)(?:\"|')",
            page, re.DOTALL)

        raw_url = match_obj.group(1)

        if not raw_url.startswith("http://"):
            url = "http://" + raw_url
        else:
            url = raw_url

        match_obj = re.search("duration\s*(?:=|:)\s*(\d+)", page, re.DOTALL)
        try:
            duration = int(match_obj.group(1))
        except:
            duration = None

        try:
            title = re.search("<title>(.+?)</title>", page, re.DOTALL).group(1)
        except:
            title = sites.get_random_text()

        self.configs = {
            "url": url,
            "title": title,
            "duration": duration
        }