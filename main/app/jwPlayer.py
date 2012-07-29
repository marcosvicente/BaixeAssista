# -*- coding: ISO-8859-1 -*-

import os, sys
import re, wx
import urllib
import string
import random
import wx.html2 as Webview
from main import settings
from django.template import Context, Template, loader, defaulttags, defaultfilters, loader_tags
########################################################################

def getPlayerPage(swf_player, flashvar):
    tmpl = loader.get_template("template-player.html")
    return tmpl.render(Context({"swf_player": swf_player, "flashvar": flashvar}))

class JWPlayer(wx.Panel):
    def __init__(self, parent, **params):
        """params = {}
        previewImage: local da imagem mostrada no backgroud do player.
        streamName: nome da stream de video sendo transferida.
        hostName: 
        portNumber: 
        skinName: 
        """
        wx.Panel.__init__(self, parent, style=0)
        self.params = params

        # defaut params
        if not params.has_key("autostart"):
            self.params["autostart"] = False

        # player reflesh
        self.swf_players = ["player_1.swf", "player_2.swf"]

        # player x skin base path
        self.playerPath = os.path.join(settings.APPDIR, "jwPlayer")

        self.skins = {}
        if not self.params.get("skinName", False):
            self.params["skinName"] = "etv" # defaut skin

        try:
            skinsPath = os.path.join(self.playerPath, "skins")
            skins = os.listdir( skinsPath )
            for name in skins:
                n = name.split(".")[0]
                self.skins[n] = name
        except: # assim, em caso de erro, teremos sempre a skin padrão
            self.skins["etv"] = "etv.zip"

        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.webview = Webview.WebView.New( self )
        self.Bind(Webview.EVT_WEB_VIEW_NAVIGATING, self.OnWebViewNavigating, self.webview)
        sizer.Add(self.webview, 1, wx.EXPAND|wx.TOP, 1)
        self.reload()

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
    
    def OnWebViewNavigating(self, evt):
        url = evt.GetURL(); evt.Veto()
        import wx.lib.agw.hyperlink as hyperlink
        hyper1 = hyperlink.HyperLinkCtrl(self)        
        hyper1.GotoURL(url)
        hyper1.Destroy()
        
    def getSkinsNames(self):
        """ retorna os nomes das skins disponiveis """
        return self.skins.keys()

    def getStreamName(self, size=25):
        letras = [char for char in string.ascii_letters]
        filename = "".join( [random.choice( letras) for i in range(size)] )
        return filename+".flv"
    
    def __setitem__(self, name, value):
        if self.params.has_key( name ):
            self.params[ name ] = value
            
    def getFlashVar(self):
        previewImage = self.params.get("previewImage", "")
        streamName = self.params.get("streamName", self.getStreamName())
        hostName = self.params.get("hostName", "localhost")
        portNumber = self.params.get("portNumber", 80)
        autostart = str(self.params["autostart"]).lower()
        # caminho completo para a skin
        skinFullPath = "file://" + os.path.join(
            self.playerPath, "skins", self.skins[ self.params["skinName"] ])

        settings = {
            "file": "http://%s:%s/%s"%(hostName, portNumber, streamName),
            "allowscriptaccess": "always", 
            "http.startparam": "start",	
            "allowfullscreen": "true", 
            "image": previewImage,
            "autostart": autostart,
            "provider": "http",
            "skin":skinFullPath,
        }
        return urllib.urlencode( settings )
    
    def reload(self):
        """ recarrega a página, atualando seu conteúdo """
        swf_player = "file://"+os.path.join(self.playerPath, self.swf_players[0])
        flashvar = self.getFlashVar()
        
        page = getPlayerPage(swf_player, flashvar)
        self.webview.SetPage(page, "")
        self.webview.Reload()
        
        self.swf_players.reverse()
        
        
########################################################################################
if __name__=='__main__':
    app = wx.App( 0 )
    frame = wx.Frame(None, -1, "JWPlayer", size = (700, 480))
    iewindow = JWPlayer( frame)
    frame.Show()
    app.MainLoop()