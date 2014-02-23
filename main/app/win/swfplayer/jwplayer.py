# -*- coding: ISO-8859-1 -*-

import os

from main import settings
from . import player


class Player(player.Player):
    defaultskin = "chelseaskin"

    template = "jwplayer.html"
    filesdirname = "jwplayer"
    playerapi = "jwplayer.js"

    # pasta com os arquivos do player
    filesdir = os.path.join(settings.STATIC_PATH, filesdirname)
    skinsdir = os.path.join(filesdir, "skins")

    flashplayer = "player-v5.10.swf"

    def __init__(self, parent, **params):
        """ params: {}
        - skinName:  local da skin do "look" dos constroles do player.
        """
        super(Player, self).__init__(parent, **params)
        self.reload()

    def getParams(self):
        params = super(Player, self).getParams()
        params["playerscript"] = "/".join([params["static"], self.filesdirname, "js", self.playerapi])
        params["provider"] = "http"
        return params