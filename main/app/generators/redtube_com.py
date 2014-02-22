# coding: utf-8
import urllib.parse

from ._sitebase import *


class Redtube(SiteBase):
    ## http://www.redtube.com/78790
    controller = {
        "url": "http://www.redtube.com/%s",
        "patterns": re.compile("(?P<inner_url>http://www.redtube.com/(?P<id>\d+))"),
        "control": "SM_SEEK",
        "video_control": None
    }

    def __init__(self, url, **params):
        """Constructor"""
        SiteBase.__init__(self, **params)
        self.basename = "redtube.com"
        self.url = url

    def random_mode(self):
        return True

    def start_extraction(self, proxies={}, timeout=25):
        fd = self.connect(self.url, proxies=proxies, timeout=timeout)
        web_page = str(fd.read())
        fd.close()

        match_obj = re.search("so\.addParam\((?:\"|')flashvars(?:\"|'),\s*(?:\"|')(.*?)(?:\"|')", web_page)
        flash_vars = match_obj.group(1)

        video_data = urllib.parse.parse_qs(flash_vars)

        try:
            title = re.search("<title>(.*?)</title>", web_page).group(1)
        except:
            title = sites.get_random_text()

        self.configs = {"url": video_data["flv_h264_url"][0] + "&ec_seek=", "title": title}