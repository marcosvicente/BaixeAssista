import re

from ._sitebase import SiteBase
from main.app.util import sites


class VidigBiz(SiteBase):
    ##
    # http://vidig.biz/embed-82bbo33w237l-518x392.html
    ##
    controller = {
        "url": "http://vidig.biz/embed-%s-518x392.html",
        "patterns": [
            re.compile("(?P<inner_url>http://vidig\.biz/embed\-(?P<id>\w+)\-\d+x\d+.html)")
        ],
        "control": "SM_SEEK",
        "video_control": None
    }

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "vidig.biz"
        self.url = url

    def start_extraction(self, proxies={}, timeout=25):
        fd = self.connect(self.url, proxies=proxies, timeout=timeout)
        web_page = str(fd.read())
        fd.close()

        print('url...')
        match_obj = re.search('file: "(.+?)"', web_page, re.DOTALL)
        url = match_obj.group(1)

        try:
            match_obj = re.search('duration: "(\d+)"', web_page, re.DOTALL)
            duration = match_obj.group(1)
        except:
            duration = 0
        title = sites.get_random_text()

        self.configs = {'title': title, 'url': url + '&start=', 'ext': 'mp4', 'duration': duration}