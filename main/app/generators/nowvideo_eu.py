# coding: utf-8
from _sitebase import *
from main.app.manager.urls import UrlManager
import videoweed_es

####################################### NOVAMOV #######################################
class NowVideo( videoweed_es.Videoweed ):
    """ Novamov: segue a mesma sequência lógica de Videoweed """
    ## http://embed.nowvideo.eu/embed.php?v=xhfpn4q7f8k3u&width=600&height=480
    ## http://www.nowvideo.eu/video/frvtqye2xed4i
    controller = {
        "url": "http://www.nowvideo.eu/video/%s",
        "basenames": ["embed.nowvideo", "nowvideo.eu"],
        "patterns": (
             re.compile("(?P<inner_url>(?:http://)?www\.nowvideo\.eu/video/(?P<id>\w+))"),
            [re.compile("(?P<inner_url>(?:http://)?embed\.nowvideo\.eu/embed\.php\?.*v=(?P<id>\w+))")]
        ),
        "control": "SM_SEEK", 
        "video_control": None
    }
    
    def __init__(self, url, **params):
        # objetos de Videoweed não anulados nessa inicialização,
        # serão considerados objetos válidos para novos objetos de Novamov.
        super(self.__class__, self).__init__(url, **params)
        
        self.player_api = "http://www.nowvideo.eu/api/player.api.php?key=%s&user=undefined&codes=1&pass=undefined&file=%s"
        # link direto para o site(não embutido)
        self.siteVideoLink = "http://embed.nowvideo.eu/embed.php?v=%s"        
        # parte principal da url usada como elemento chave no programa
        self.basename = UrlManager.getBaseName( url )
        self.url = url
        
        