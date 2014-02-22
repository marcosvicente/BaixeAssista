# coding: utf-8
from html.parser import HTMLParser
import re
import urllib

from ._sitebase import SiteBase
from main.app.generators import Universal
from main.app.util import sites


class Dailymotion(SiteBase):
    """Information Extractor for Dailymotion"""
    ## http://www.dailymotion.com/video/xowm01_justin-bieber-gomez-at-chuck-e-cheese_news#
    controller = {
        "url": "http://www.dailymotion.com/video/%s",
        "patterns": re.compile(
            r"(?P<inner_url>(?i)(?:https?://)?(?:www\.)?dailymotion(?:\.com)?(?:[a-z]{2,3})?/video/(?P<id>.+))"),
        "control": "SM_RANGE",
        "video_control": None
    }

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "dailymotion.com"
        self.url = url

    def start_extraction(self, proxies={}, timeout=25):
        video_id = Universal.get_video_id(self.basename, self.url)
        fd = self.connect(self.url, proxies=proxies, timeout=timeout, headers={'Cookie': 'family_filter=off'})
        web_page = fd.read()
        fd.close()

        video_extension = 'flv'

        # Extract URL, uploader and title from web_page
        match_obj = re.search(r'addVariable\(\"sequence\"\s*,\s*\"(.+?)\"\)', web_page, re.DOTALL | re.IGNORECASE)

        sequence = urllib.parse.unquote(match_obj.group(1))
        match_obj = re.search(r',\"sdURL\"\:\"([^\"]+?)\",', sequence)
        media_url = urllib.parse.unquote(match_obj.group(1)).replace('\\', '')

        # if needed add http://www.dailymotion.com/ if relative URL
        video_url = media_url

        try:
            html_parser = HTMLParser()
            match_obj = re.search(r'<meta property="og:title" content="(?P<title>[^"]*)" />', web_page)
            video_title = html_parser.unescape(match_obj.group('title'))
        except:
            video_title = sites.get_random_text()

        matchobj = re.search(r'(?im)<span class="owner[^\"]+?">[^<]+?<a [^>]+?>([^<]+?)</a></span>', web_page)
        video_uploader = matchobj.group(1)

        self.configs = {
            'id': video_id.decode('utf-8'),
            'url': video_url.decode('utf-8'),
            'uploader': video_uploader.decode('utf-8'),
            'upload_date': 'NA',
            'title': video_title,
            'ext': video_extension,
            'format': 'NA',
            'player_url': None,
        }