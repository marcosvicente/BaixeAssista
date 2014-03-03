# coding: utf-8
import json
import re
import urllib.parse

from ._sitebase import SiteBase
from main.app.generators import Universal
from main.app.util import sites


class MoeVideo(SiteBase):
    ##
    # http://moevideo.net/video.php?file=64141.60e02b3b80c5e95e2e4ac85f0838&width=600&height=450
    # http://moevideo.net/?page=video&uid=79316.7cd2a2d4b5e02fd77f017bbc1f01
    ##
    controller = {
        "url": "http://moevideo.net/video.php?file=%s",
        "patterns": (
            re.compile("(?P<inner_url>http://moevideo\.net/\?page=video&uid=(?P<id>\w+\.\w+))"),
            [re.compile("(?P<inner_url>http://moevideo\.net/video\.php\?file=(?P<id>\w+\.\w+))")]
        ),
        "control": "SM_RANGE",
        "video_control": None
    }

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.api_url = "http://api.letitbit.net/"
        self.basename = "moevideo.net"
        self.url = url

    def random_mode(self):
        return True

    @staticmethod
    def get_post_data(video_id):
        encoder = json.JSONEncoder()
        post = {"r": encoder.encode(
            ["tVL0gjqo5",
             ["preview/flv_image", {"uid": "%s" % video_id}],
             ["preview/flv_link", {"uid": "%s" % video_id}]])
        }
        return urllib.parse.urlencode(post)

    @staticmethod
    def get_link_(data):
        link = ""
        if data["status"].lower() == "ok":
            for info in data["data"]:
                if type(info) is dict and "link" in info:
                    link = info["link"]
                    break
        return link

    @staticmethod
    def get_title_(url):
        title = url.rsplit("/", 1)[-1]
        title = title.rsplit(".", 1)[0]
        return title

    def set_message(self, url, data):
        if not url:
            if data["status"].lower() == "fail":
                msg = data["data"]
            else:
                if "not_found" in data["data"]:
                    msg = "file not found"
                else:
                    msg = data["data"][0]
            self.message = msg

    def start_extraction(self, proxies={}, timeout=25):
        video_id = Universal.get_video_id(self.basename, self.url)
        request = self.connect(self.api_url, proxies=proxies, timeout=timeout, data=self.get_post_data(video_id))
        json_data = request.json()
        request.close()

        url = self.get_link_(json_data)

        try:
            self.set_message(url, json_data)
        except:
            pass
        # obtendo o título do video
        try:
            title = self.get_title_(url)
        except:
            title = sites.get_random_text()

        self.configs = {"url": url, "title": title}