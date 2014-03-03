# coding: utf-8
import re
import urllib.parse

from ._sitebase import SiteBase
from main.app.generators import Universal
from main.app.util import sites


class Metacafe(SiteBase):
    """ Information Extractor for metacafe.com """
    ##
    # http://www.metacafe.com/watch/8492972/wheel_of_fortune_fail/
    ##
    controller = {
        "url": "http://www.metacafe.com/watch/%s/",
        "patterns": re.compile("(?P<inner_url>(?:http://)?www\.metacafe\.com/watch/(?P<id>\w+)/.*)"),
        "control": "SM_RANGE",
        "video_control": None
    }

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "metacafe.com"
        self.url = url

    def get_link(self):
        video_quality = int(self.params.get("quality", 2))
        when_not_found = self.configs.get(1, None)
        when_not_found = self.configs.get(2, when_not_found)
        when_not_found = self.configs.get(3, when_not_found)
        return self.configs.get(video_quality, when_not_found)

    def start_extraction(self, proxies={}, timeout=25):
        video_id = Universal.get_video_id(self.basename, self.url)

        url = "http://www.metacafe.com/watch/%s/" % video_id
        request = self.connect(url, proxies=proxies, timeout=timeout)
        page = request.text
        request.close()

        matchobj = re.search("flashVarsCache\s*=\s*\{(.*?)\}", page)
        flashvars = urllib.parse.unquote_plus(matchobj.group(1))

        matchobj = re.search(
            "\"mediaData\".+?\"mediaURL\"\s*:\s*\"(.*?)\".*\"key\"\s*:\s*\"(.*?)\".*\"value\"\s*:\s*\"(.*?)\"",
            flashvars)

        low_url = urllib.parse.unquote_plus(matchobj.group(1)) + "?%s=%s" % (matchobj.group(2), matchobj.group(3))
        low_url = low_url.replace("\/", "/")

        matchobj = re.search(
            "\"highDefinitionMP4\".+?\"mediaURL\"\s*:\s*\"(.*?)\".*\"key\"\s*:\s*\"(.*?)\".*\"value\"\s*:\s*\"(.*?)\"",
            flashvars)

        high_url = urllib.parse.unquote_plus(matchobj.group(1)) + "?%s=%s" % (matchobj.group(2), matchobj.group(3))
        high_url = high_url.replace("\/", "/")

        try:
            title = re.search("<title>(.+)</title>", page).group(1)
        except:
            title = sites.get_random_text()

        self.configs = {'title': title, 1: low_url, 2: high_url}