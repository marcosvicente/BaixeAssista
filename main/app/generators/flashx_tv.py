# coding: utf-8
import os
import re

from ._sitebase import SiteBase
from main.app.generators import Universal
from main.app.util import sites


class FlashxTv(SiteBase):
    ##
    # http://play.flashx.tv/nuevo/player/cst.php?hash=1AB71XOUKW77
    # http://flashx.tv/video/18U57YS4698X/REM-Blue
    # http://play.flashx.tv/player/embed.php?hash=1AB71XOUKW77
    # http://play.flashx.tv/player/embed.php?vid=401804&width=620&height=400&autoplay=no
    ##
    controller = {
        "url": "http://flashx.tv/video/%s",
        "basenames": ["play.flashx", "flashx.tv"],
        "patterns": (
            re.compile("(?P<inner_url>http://flashx\.tv/video/(?P<id>\w+)/(?:\w+)?)"),
            [re.compile("(?P<inner_url>http://play\.flashx\.tv/player/embed\.php\?(?:hash|vid)=(?P<id>\w+))")],
        ),
        "control": "SM_SEEK",
        "video_control": None
    }
    xml_link = "http://play.flashx.tv/nuevo/player/cst.php?hash=%s"

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "flashx.tv"
        self.url = url

    def random_mode(self):
        return True

    def start_extraction(self, proxies={}, timeout=25):
        if Universal.isEmbed(self.url) and re.match(".+embed\.php\?vid=", self.url):
            request = self.connect(self.url, proxies=proxies, timeout=timeout)
            page = request.text
            request.close()
            video_id = re.search("hash=(\w+)&", page, re.DOTALL).group(1)
        else:
            video_id = Universal.get_video_id(self.basename, self.url)
            page = None

        request = self.connect(self.xml_link % video_id, proxies=proxies, timeout=timeout)
        xml_data = request.text
        request.close()

        matchobj = re.search("<file>(.+)</file>", xml_data, re.DOTALL)
        url = matchobj.group(1)

        try:
            http_params = re.search("<httpparam>(.+)</httpparam>", xml_data, re.DOTALL)
            http_params = "?%s=" % http_params.group(1)
        except:
            http_params = "?start="

        if page is None:
            try:
                title = os.path.basename(self.url)
            except:
                title = sites.get_random_text()
        else:
            try:
                title = re.search("<title>(.+)</title>", page, re.DOTALL).group(1)
            except:
                title = sites.get_random_text()

        self.configs = {"url": url + http_params, "title": title}