# -*- coding: ISO-8859-1 -*-

import os
from main import settings
import player

# -----------------------------------------------------------------------------
class Player( player.Player ):
    defaultskin = "BlackWhite"
    
    template = "flowplayer.html"
    filesdirname = "flowplayer"
    playerapi = "flowplayer-3.2.11.min.js"
    
    # pasta com os arquivos do player
    filesdir = os.path.join(settings.STATIC_PATH, filesdirname)
    skinsdir = os.path.join(filesdir, "skins")
    
    flashplayer = "player-v3.2.15.swf"
    
    def __init__(self, parent, **params):
        """ params: {}
        - skinName:  local da skin do "look" dos constroles do player.
        """
        super(Player, self).__init__(parent, **params)
        self.reload()
     
    def getParams(self):
        params = super(Player, self).getParams()
        params["pluginskin"] = "/".join([params["static"], self.filesdirname, 
                                         "plugins/flowplayer.pseudostreaming-3.2.11.swf"])
        return params
    
    
    
