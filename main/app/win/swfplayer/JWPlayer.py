# -*- coding: ISO-8859-1 -*-

import os
from main import settings
import player

# -----------------------------------------------------------------------------
class Player( player.Player ):
    defaultskin = "etv"
    
    template = "jwplayer.html"
    filesdirname = "jwplayer"
    playerapi = "jwplayer.js"
    
    # pasta com os arquivos do player
    filesdir = os.path.join(settings.STATIC_PATH, filesdirname)
    skinsdir = os.path.join(filesdir, "skins")
    
    swf_players = ["jwplayer.flash-1.swf", "jwplayer.flash-2.swf"]
    
    def __init__(self, parent, **params):
        """ params: {}
        - skinName:  local da skin do "look" dos constroles do player.
        """
        super(Player, self).__init__(parent, **params)
        self.reload()
     
    def getParams(self):
        params = super(Player, self).getParams()
        params["provider"] = "http"
        
        apiUrl = "/".join([params["staticurl"], self.filesdirname, self.playerapi])
        params["playerscript"] = apiUrl
        return params