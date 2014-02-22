# coding: utf-8
from . import putlocker_com
import re


class Sockshare(putlocker_com.PutLocker):
    ## http://www.sockshare.com/file/E6DDA74FBBBFFC12
    ## http://www.sockshare.com/embed/E6DDA74FBBBFFC12
    controller = {
        "url": "http://www.sockshare.com/file/%s",
        "patterns": (
            re.compile("(?P<inner_url>(?:http://)?www\.sockshare\.com/file/(?P<id>\w+))"),
            [re.compile("(?P<inner_url>(?:http://)?www\.sockshare\.com/embed/(?P<id>\w+))")]
        ),
        "control": "SM_RANGE",
        "video_control": None
    }

    def __init__(self, url, **params):
        super(self.__class__, self).__init__(url, **params)
        self.getFileBaseUrl = "http://www.sockshare.com"
        self.basename = "sockshare.com"
        self.url = url