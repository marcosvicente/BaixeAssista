# coding: utf-8
from ._sitebase import *


class Videomega(SiteBase):
    # http://videomega.tv/iframe.php?ref=OEKgdSTMGQ&width=505&height=4
    controller = {
        "url": "http://videomega.tv/iframe.php?ref=%s",
        "patterns": [re.compile(
            "(?P<inner_url>http://videomega\.tv/iframe\.php\?ref=(?P<id>\w+)(?:&width=\d+)?(&height=\d+)?)")],
        "control": "SM_RANGE",
        "video_control": None
    }

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.url = url

    def suportaSeekBar(self):
        return True

    def start_extraction(self, proxies={}, timeout=25):
        fd = self.connect(self.url, proxies=proxies, timeout=timeout)
        web_page = fd.read()
        fd.close()

        match_obj = re.search("unescape\s*\((?:\"|')(.+)(?:\"|')\)", web_page)
        settings = urllib.parse.unquote_plus(match_obj.group(1))

        match_obj = re.search("file\s*:\s*(?:\"|')(.+?)(?:\"|')", settings)
        url = match_obj.group(1)

        try:
            title = re.search("<title>(.+)</title>", web_page).group(1)
        except:
            title = sites.get_random_text()

        self.configs = {"url": url, "title": title}  #+"&start="