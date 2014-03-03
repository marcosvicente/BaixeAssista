# coding: utf-8
import base64
import re
import urllib.parse

from ._sitebase import SiteBase
from main.app.generators import Universal
from main.app.util import sites


class Pornhub(SiteBase):
    # http://www.pornhub.com/view_video.php?viewkey=1156461684&utm_source=embed&utm_medium=embed&utm_campaign=embed-logo
    controller = {
        "url": "http://www.pornhub.com/view_video.php?viewkey=%s",
        "patterns": (
            re.compile("(?P<inner_url>http://www\.pornhub\.com/view_video\.php\?viewkey=(?P<id>\w+))"),
            [re.compile(
                "(?P<inner_url>http://www\.pornhub\.com/view_video\.php\?viewkey=(?P<id>\w+).*&utm_source=embed)")]
        ),
        "control": "SM_SEEK",
        "video_control": None
    }

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.apiUrl = "http://www.pornhub.com/embed_player.php?id=%s"
        self.basename = "pornhub.com"
        self.url = url

    def random_mode(self):
        return True

    def start_extraction(self, proxies={}, timeout=25):
        request = self.connect(self.url, proxies=proxies, timeout=timeout)
        page = request.text
        request.close()
        try:
            fs = ""
            matchobj = re.search('''(?:"|')video_url(?:"|')\s*:\s*(?:"|')(.+?)(?:"|')''', page, re.DOTALL)
            try:
                url = base64.b64decode(urllib.parse.unquote_plus(matchobj.group(1)))
            except:
                url = urllib.parse.unquote_plus(matchobj.group(1))

            matchobj = re.search('''(?:"|')video_title(?:"|')\s*:\s*(?:"|')(.*?)(?:"|')''', page, re.DOTALL)
            try:
                title = urllib.parse.unquote_plus(matchobj.group(1))
            except:
                title = sites.get_random_text()
        except:
            url_id = Universal.get_video_id(self.basename, self.url)
            request = self.connect(self.apiUrl % url_id, proxies=proxies, timeout=timeout)
            xml_data = request.text
            request.close()

            url = re.search("""<video_url><!\[CDATA\[(.+)\]\]></video_url>""", xml_data).group(1)

            try:
                title = re.search("<video_title>(.*)</video_title>", xml_data).group(1)
            except:
                title = sites.get_random_text()

            try:
                fs = re.search("<flvStartAt>(.+)</flvStartAt>", xml_data).group(1)
            except:
                fs = ''

        self.configs = {"url": url + (fs or "&fs="), "title": (title or sites.get_random_text())}