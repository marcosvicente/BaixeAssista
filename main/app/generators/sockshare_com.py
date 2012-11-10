from putlocker_com import *

###################################### PUTLOCKER ######################################
class Sockshare( PutLocker ):
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
        PutLocker.__init__(self, url, **params)
        self.getFileBaseUrl = "http://www.sockshare.com"
        self.basename = "sockshare.com"
        self.url = url