from _sitebase import *

####################################### NOVAMOV #######################################
class NowVideo( Videoweed ):
    """ Novamov: segue a mesma sequ�ncia l�gica de Videoweed """
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
        """Constructor"""
        # objetos de Videoweed n�o anulados nessa inicializa��o,
        # ser�o considerados objetos v�lidos para novos objetos de Novamov.
        Videoweed.__init__(self, url, **params)
        self.player_api = "http://www.nowvideo.eu/api/player.api.php?key=%s&user=undefined&codes=1&pass=undefined&file=%s"
        # link direto para o site(n�o embutido)
        self.siteVideoLink = "http://embed.nowvideo.eu/embed.php?v=%s"        
        # parte principal da url usada como elemento chave no programa
        self.basename = manager.UrlManager.getBaseName( url )
        self.url = url