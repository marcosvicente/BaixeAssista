# -*- coding: ISO-8859-1 -*-

import os
from main import settings
import player
import wx

# -----------------------------------------------------------------------------
class Player( player.Player ):
    defaultskin = "BlackWhite"
    
    template = "flowplayer.html"
    filesdirname = "flowplayer"
    
    # pasta com os arquivos do player
    filesdir = os.path.join(settings.STATIC_PATH, filesdirname)
    skinsdir = os.path.join(filesdir, "skins")
    
    swf_players = ["flowplayer-3.2.15-1.swf", "flowplayer-3.2.15-2.swf"]
    
    def __init__(self, parent, **params):
        """ params: {}
        - skinName:  local da skin do "look" dos constroles do player.
        """
        super(Player, self).__init__(parent, **params)
        self.reload()
     
    def getParams(self):
        params = super(Player, self).getParams()
        params["pluginskin"] = "/".join([params["staticurl"], 
            self.filesdirname, "plugins/flowplayer.pseudostreaming-3.2.11.swf"
        ])
        return params
        
# -----------------------------------------------------------------------------
if __name__=='__main__':
    app = wx.App( 0 )
    frame = wx.Frame(None, -1, "Player", size = (700, 480))
    iewindow = Player( frame)
    frame.Show()
    app.MainLoop()
    
    
    
