# coding: utf-8
from ._sitebase import *


class MyVideo(SiteBase):
    """ Information Extractor for myvideo.de """
    # http://www.myvideo.de/watch/8532190/D_Gray_man_Folge_2_Der_Schwarze_Orden
    controller = {
        "url": "http://www.myvideo.de/watch/%s",
        "patterns": re.compile(r'(?P<inner_url>(?:http://)?(?:www\.)?myvideo\.de/watch/(?P<id>[0-9]+)/(?:[^?/]+)?.*)'),
        "control": "SM_RANGE",
        "video_control": None
    }

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "myvideo.de"
        self.url = url

    def start_extraction(self, proxies={}, timeout=25):
        video_id = Universal.get_video_id(self.basename, self.url)
        url = 'http://www.myvideo.de/watch/%s' % video_id

        fd = self.connect(url, proxies=proxies, timeout=timeout)
        web_page = fd.read()
        fd.close()

        match_obj = re.search(
            r'<link rel=\'image_src\' href=\'(http://is[0-9].myvideo\.de/de/movie[0-9]+/[a-f0-9]+)/thumbs/[^.]+\.jpg\' />',
            web_page)
        video_url = match_obj.group(1) + ('/%s.flv' % video_id)

        try:
            video_title = re.search('<title>([^<]+)</title>', web_page).group(1)
        except:
            video_title = sites.get_random_text()

        self.configs = {
            'id': video_id,
            'url': video_url,
            'uploader': 'NA',
            'upload_date': 'NA',
            'title': video_title,
            'ext': 'flv',
            'format': 'NA',
            'player_url': None,
        }