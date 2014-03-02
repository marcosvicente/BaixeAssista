# -*- coding: ISO-8859-1 -*-

import os

from main import settings
from . import player


class Player(player.Player):
    skin = "BlackWhite"

    template = "flowplayer.html"
    media = "flowplayer"
    js_api = "flowplayer-3.2.11.min.js"

    # pasta com os arquivos do player
    media_path = os.path.join(settings.STATIC_PATH, media)
    skin_path = os.path.join(media_path, "skins")

    swf_player = "player-v3.2.15.swf"

    def __init__(self, parent, **params):
        """ params: {}
        - skinName:  local da skin do "look" dos constroles do player.
        """
        super(Player, self).__init__(parent, **params)
        self.reload()

    def get_params(self):
        params = super(Player, self).get_params()
        params["pluginskin"] = "/".join([
            params["static"], self.media,
            "plugins/flowplayer.pseudostreaming-3.2.11.swf"
        ])
        return params