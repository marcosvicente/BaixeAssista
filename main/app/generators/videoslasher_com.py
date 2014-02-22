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

    def suportaSeekBar(self):
        return True

    def postPage(self, web_page, proxies, timeout):
        matchobj = putlocker_com.PutLocker.pattern_form.search(web_page)

        hash_value = matchobj.group("hash") or matchobj.group("hash_second")
        hash_name = matchobj.group("name") or matchobj.group("name_second")
        confirm = matchobj.group("confirm")

        data = urllib.parse.urlencode({hash_name: hash_value, "confirm": confirm})
        fd = self.connect(self.url, proxies=proxies, timeout=timeout, data=data)
        web_page = fd.read()
        fd.close()
        return web_page

    def start_extraction(self, proxies={}, timeout=25):
        fd = self.connect(self.url, proxies=proxies, timeout=timeout)
        web_page = fd.read()
        fd.close()

        try:
            web_page = self.postPage(web_page, proxies, timeout)
        except:
            web_page = web_page

        matchobj = re.search("""playlist:\s*(?:'|")(/playlist/\w+)(?:'|")""", web_page, re.DOTALL)
        playlist_url = matchobj.group(1)

        if not playlist_url.endswith('/'):
            playlist_url += '/'

        fd = self.connect(self.domain + playlist_url, proxies=proxies, timeout=timeout)
        rss_data = fd.read()
        fd.close()

        for item in re.findall("<item>(.+?)</item>", rss_data, re.DOTALL):
            matchobj = re.search('''\<media:content\s*url\s*=\s*"(.+?)"\s*type="video.+?"''', item, re.DOTALL)
            if matchobj:
                url = matchobj.group(1)
                break
        else:
            raise Exception

        try:
            title = re.search("<title>(.+?)</title>", web_page, re.DOTALL).group(1)
        except:
            title = sites.get_random_text()

        self.configs = {"url": url + "&start=", "title": title}