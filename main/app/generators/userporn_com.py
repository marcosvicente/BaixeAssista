# coding: utf-8
from ._sitebase import *
from . import videobb_com


class Userporn(videobb_com.Videobb):
    ##
    # http://www.userporn.com/video/WZ8Nuf2blzw8
    # http://www.userporn.com/watch_video.php?v=WZ8Nuf2blzw8
    ##
    controller = {
        "url": "http://www.userporn.com/video/%s",
        "patterns": re.compile(
            "(?P<inner_url>(?:http://)?(?:www\.)?userporn\.com/(?:video/|watch_video\.php\?v=)(?P<id>\w+))"),
        "control": "SM_RANGE",
        "video_control": None
    }

    def __init__(self, url, **params):
        super(self.__class__, self).__init__(url, **params)
        self.settings_url = "http://www.userporn.com/player_control/settings.php?v=%s"
        self.key2 = 526729