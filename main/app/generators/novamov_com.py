from _sitebase import *

####################################### NOVAMOV #######################################
class Novamov( Videoweed ):
    """ Novamov: segue a mesma sequência lógica de Videoweed """
    ## http://www.novamov.com/video/cfqxscgot96pe
    ## http://embed.novamov.com/embed.php?width=520&height=320&v=cfqxscgot96pe&px=1
    controller = {
        "url": "http://www.novamov.com/video/%s", 
        "basenames": ["novamov.com", "embed.novamov"],
        "patterns": (
             re.compile("(?P<inner_url>(?:http://)?www\.novamov\.com/video/(?P<id>\w+))"),
            [re.compile("(?P<inner_url>(?:http://)?embed\.novamov\.com/embed\.php\?.*v=(?P<id>\w+))")]
        ),
        "control": "SM_SEEK", 
        "video_control": None
    }
    
    def __init__(self, url, **params):
        """Constructor"""
        # objetos de Videoweed não anulados nessa inicialização,
        # serão considerados objetos válidos para novos objetos de Novamov.
        Videoweed.__init__(self, url, **params)
        self.player_api = "http://www.novamov.com/api/player.api.php?key=%s&user=undefined&codes=1&pass=undefined&file=%s"
        # link direto para o site(não embutido)
        self.siteVideoLink = "http://www.novamov.com/video/%s"        
        # parte principal da url usada como elemento chave no programa
        self.basename = manager.UrlManager.getBaseName( url )
        self.url = url