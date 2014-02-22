import re
import urllib.parse

from ._sitebase import SiteBase

from main.app.util import sites


class Xvideos(SiteBase):
    ## http://www.xvideos.com/video2037621/mommy_and_daughter_spreading
    controller = {
        "url": "http://www.xvideos.com/%s",
        "patterns": re.compile("(?P<inner_url>http://www.xvideos.com/(?P<id>video\w+)(?:/\w+)?)"),
        "control": "SM_SEEK",
        "video_control": None
    }

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "xvideos.com"
        self.url = url

    def random_mode(self):
        return True

    def start_extraction(self, proxies={}, timeout=25):
        fd = self.connect(self.url, proxies=proxies, timeout=timeout)
        web_page = str(fd.read())
        fd.close()

        match_obj = re.search('\<embed\s*type.+flashvars="(.*?)"', web_page)
        flash_vars = match_obj.group(1)

        video_data = urllib.parse.parse_qs(flash_vars)

        try:
            title = re.search("<title>(.*?)</title>", web_page).group(1)
        except:
            title = sites.get_random_text()

        self.configs = {"url": video_data["flv_url"][0] + "&fs=", "title": title}