# coding: utf-8
import re
import urllib.parse

from ._sitebase import SiteBase
from main.app.generators import Universal


class GoogleVideo(SiteBase):
    """ Information extractor for video.google.com """
    # http://video.google.com.br/videoplay?docid=-1717800235769991478
    controller = {
        "url": "http://video.google.com.br/videoplay?docid=%s",
        "patterns": re.compile(
            r'(?P<inner_url>(?:http://)?video\.google\.(?:com(?:\.au)?(?:\.br)?|co\.(?:uk|jp|kr|cr)|ca|de|es|fr||it|nl|pl)/videoplay\?docid=(?P<id>-?[^\&]+).*)'),
        "control": "SM_RANGE",
        "video_control": None
    }

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "video.google"
        self.url = url

    def start_extraction(self, proxies={}, timeout=25):
        video_id = Universal.get_video_id(self.basename, self.url)

        url = "http://video.google.com/videoplay?docid=%s&hl=en&oe=utf-8" % video_id
        fd = self.connect(url, proxies=proxies, timeout=timeout)
        web_page = fd.read()
        fd.close()

        video_extension = "mp4"

        # Extract URL, uploader, and title from web_page
        match_obj = re.search(r"download_url:'([^']+)'", web_page)
        if match_obj is None:
            video_extension = 'flv'
            match_obj = re.search(r"(?i)videoUrl\\x3d(.+?)\\x26", web_page)
        if match_obj is None:
            return

        media_url = urllib.parse.unquote(match_obj.group(1))
        media_url = media_url.replace('\\x3d', '\x3d')
        media_url = media_url.replace('\\x26', '\x26')

        video_url = media_url

        match_obj = re.search(r'<title>(.*)</title>', web_page)
        if match_obj is None: return

        video_title = match_obj.group(1).decode('utf-8')

        self.configs = {
            'id': video_id.decode('utf-8'),
            'url': video_url.decode('utf-8'),
            'uploader': 'NA',
            'upload_date': 'NA',
            'title': video_title,
            'ext': video_extension,
            'format': 'NA',
            'player_url': None,
        }