# coding: utf-8
from _sitebase import *
import videobb_com

###################################### VIDEOZER #######################################
class Videozer( videobb_com.Videobb ):
    ## http://www.videozer.com/video/ceN9vZXa
    controller = {
        "url": "http://www.videozer.com/video/%s", 
        "patterns": re.compile("(?P<inner_url>(?:http://)?(?:www\.)?videozer\.com/video/(?P<id>\w+))"), 
        "control": "SM_SEEK", 
        "video_control": None
    }
    
    def __init__(self, url, **params):
        super(self.__class__, self).__init__(url, **params)
        self.settingsLink = 'http://www.videozer.com/player_control/settings.php?v=%s&fv=v1.1.14'
        self.env = ["cfg","environment"]
        self.res = ["cfg","quality"]
        self.key2 = 215678

    def get_sece2(self, params):
        return params["cfg"]["info"]["sece2"]

    def get_title(self, params):
        return params["cfg"]["info"]["video"]["title"]

    def get_gads(self, params):
        return params["cfg"]["ads"]["g_ads"]

    def get_rkts(self, params):
        return params[self.env[0]][self.env[1]]["rkts"]

    def get_spn(self, params):
        return params["cfg"]["login"]["spn"]
