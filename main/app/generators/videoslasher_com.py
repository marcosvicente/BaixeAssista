# coding: utf-8
import re
import urllib.parse

from ._sitebase import SiteBase
from . import putlocker_com
from main.app.util import sites


class Videoslasher(SiteBase):
    ##
    # http://www.videoslasher.com/video/6O9TSHUUR4UY == http://www.videoslasher.com/embed/6O9TSHUUR4UY
    ##
    controller = {
        "url": "http://www.videoslasher.com/video/%s",
        "patterns": (
            re.compile("(?P<inner_url>http://www\.videoslasher\.com/video/(?P<id>\w+))"),
            [re.compile("(?P<inner_url>http://www\.videoslasher\.com/embed/(?P<id>\w+))")]
        ),
        "control": "SM_SEEK",
        "video_control": None
    }
    domain = "http://www.videoslasher.com"

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "videoslasher.com"
        self.url = url

    def random_mode(self):
        return True

    def post_page(self, page, proxies, timeout):
        matchobj = putlocker_com.PutLocker.pattern_form.search(page)

        hash_value = matchobj.group("hash") or matchobj.group("hash_second")
        hash_name = matchobj.group("name") or matchobj.group("name_second")
        confirm = matchobj.group("confirm")

        data = urllib.parse.urlencode({hash_name: hash_value, "confirm": confirm})

        request = self.connect(self.url, proxies=proxies, timeout=timeout, data=data)
        page = request.text
        request.close()
        return page

    def start_extraction(self, proxies={}, timeout=25):
        request = self.connect(self.url, proxies=proxies, timeout=timeout)
        page = request.text
        request.close()

        try:
            page = self.post_page(page, proxies, timeout)
        except:
            page = page

        match_obj = re.search("playlist:\s*(?:'|\")(/playlist/\w+)(?:'|\")", page, re.DOTALL)
        playlist_url = match_obj.group(1)

        if not playlist_url.endswith('/'):
            playlist_url += '/'

        request = self.connect(self.domain + playlist_url, proxies=proxies, timeout=timeout)
        rss_data = request.text
        request.close()

        for item in re.findall("<item>(.+?)</item>", rss_data, re.DOTALL):
            match_obj = re.search('''\<media:content\s*url\s*=\s*"(.+?)"\s*type="video.+?"''', item, re.DOTALL)
            if match_obj:
                url = match_obj.group(1)
                break
        else:
            raise Exception

        try:
            title = re.search("<title>(.+?)</title>", page, re.DOTALL).group(1)
        except:
            title = sites.get_random_text()

        self.configs = {"url": url + "&start=", "title": title}