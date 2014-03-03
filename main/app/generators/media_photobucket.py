# coding: utf-8
import re
import urllib.parse

from ._sitebase import SiteBase
from main.app.util import sites


class Photobucket(SiteBase):
    """ Information extractor for photobucket.com """
    ## http://photobucket.com/videos
    controller = {
        "url": "http://media.photobucket.com/video/%s",
        "patterns": re.compile("(?P<inner_url>(?:http://)?media\.photobucket\.com/video/(?P<id>.*))"),
        "control": "SM_RANGE",
        "video_control": None
    }

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "media.photobucket"
        self.url = url

    def start_extraction(self, proxies={}, timeout=25):
        request = self.connect(self.url, proxies=proxies, timeout=timeout)
        page = request.text
        request.close()
        video_extension = 'flv'

        # Extract URL, uploader, and title from web_page
        matchobj = re.search(r'<link rel="video_src" href=".*\?file=([^"]+)" />', page)
        media_url = urllib.parse.unquote(matchobj.group(1))
        video_url = media_url

        try:
            matchobj = re.search(r'<meta name="description" content="(.+)"', page)
            video_title = matchobj.group(1).decode('utf-8')
        except:
            video_title = sites.get_random_text()

        self.configs = {
            'url': video_url,
            'upload_date': 'NA',
            'title': video_title,
            'ext': video_extension,
            'format': 'NA',
            'player_url': None
        }