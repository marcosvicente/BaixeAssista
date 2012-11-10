# coding: utf-8
from videobb_com import *

###################################### USERPORN #######################################
class Userporn( Videobb ):
    ## http://www.userporn.com/video/WZ8Nuf2blzw8
    ## http://www.userporn.com/watch_video.php?v=WZ8Nuf2blzw8
    controller = {
        "url": "http://www.userporn.com/video/%s", 
        "patterns": re.compile("(?P<inner_url>(?:http://)?(?:www\.)?userporn\.com/(?:video/|watch_video\.php\?v=)(?P<id>\w+))"), 
        "control": "SM_SEEK",
        "video_control": None
    }

    def __init__(self, url, **params):
        Videobb.__init__(self, url, **params)
        self.settingsLink = "http://www.userporn.com/player_control/settings.php?v=%s"
        self.key2 = 526729