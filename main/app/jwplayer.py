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

class Player(wx.Panel):
    playerMedia = os.path.join(settings.STATIC_PATH, "jwplayer")
    swf_players = ["player-5.10-1.swf", "player-5.10-2.swf"]
    defaultSkin = "etv"
    
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
        self.skins = {}
        
        # defaut params
        if not params.has_key("autostart"): self.params["autostart"] = False
        if not params.has_key("skinName"): self.params["skinName"] = self.defaultSkin
        if not params.has_key("hostName"): self.params["hostName"] = "localhost"
        if not params.has_key("portNumber"): self.params["portNumber"] = 80
        
        try:
            skinsPath = os.path.join(self.playerMedia, "skins")
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
        
    @staticmethod
    def getPlayerPage( params ):
        tmpl_dir = os.path.join(settings.APPDIR, "templates")
        try: tmpl = loader.find_template("jwplayer.html", dirs=(tmpl_dir,))[0]
        except: tmpl = loader.get_template(os.path.join(tmpl_dir, "jwplayer.html"))
        return tmpl.render(Context({"params": params}))
        
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
            
    def get_params(self):
        previewImage = self.params.get("previewImage", "")
        streamName = self.params.get("streamName", self.getStreamName())
        hostName = self.params.get("hostName", "localhost")
        portNumber = self.params.get("portNumber", 80)
        autostart = str(self.params["autostart"]).lower()
        
        hostDomain = "http://%s:%s"%(hostName, portNumber)
        staticUrl = hostDomain +"/static"
        streamFile = hostDomain+"/" +streamName
        
        # caminho completo para a skin
        skinName = self.skins.get(self.params["skinName"], self.defaultSkin)
        skinPath = staticUrl + "/jwplayer/skins/" + skinName
        swfPlayer = staticUrl +"/jwplayer/" + self.swf_players[0]
        self.swf_players.reverse()
        
        params = {
            "file": streamFile,
            "swfPlayer": swfPlayer,
            "allowscriptaccess": "always", 
            "startparam": "start",	
            "allowfullscreen": "true", 
            "image": previewImage,
            "autostart": autostart,
            "provider": "http",
            "skin": skinPath,
        }
        return params
    
    def reload(self):
        """ recarrega a página, atualando seu conteúdo """
        page = self.getPlayerPage( self.get_params() )
        self.webview.SetPage(page, "Loader")
        self.webview.Reload()
        
########################################################################################
if __name__=='__main__':
    app = wx.App( 0 )
    frame = wx.Frame(None, -1, "Player", size = (700, 480))
    iewindow = Player( frame)
    frame.Show()
    app.MainLoop()