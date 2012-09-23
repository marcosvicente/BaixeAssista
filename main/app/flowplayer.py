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
        
        # arquivo do swf player
        self.swf_players = ["flowplayer-3.2.15-1.swf", "flowplayer-3.2.15-2.swf"]
        
        # pasta de arquivos do player
        self.playerMedia = os.path.join(settings.STATIC_PATH, "flowplayer")
        
        self.skins = {}
        self.defaultSkin = "BlackWhite"
        
        if not self.params.get("skinName", False):
            self.params["skinName"] = self.defaultSkin
            
        try:
            skinsPath = os.path.join(self.playerMedia, "skins")
            skins = os.listdir( skinsPath )
            for name in skins:
                n = name.split(".",1)[0]
                self.skins[n] = name
        except: # assim, em caso de erro, teremos sempre a skin padrão
            self.skins["BlackWhite"] = "BlackWhite.swf"
            
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.webview = Webview.WebView.New( self )
        self.Bind(Webview.EVT_WEB_VIEW_NAVIGATING, self.OnWebViewNavigating, self.webview)
        sizer.Add(self.webview, 1, wx.EXPAND)
        self.reload()
        
        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        
    @staticmethod
    def getPlayerPage( params ):
        tmpl_dir = os.path.join(settings.APPDIR, "templates")
        try: tmpl = loader.find_template("flowplayer.html", dirs=(tmpl_dir,))[0]
        except: tmpl = loader.get_template(os.path.join(tmpl_dir, "flowplayer.html"))
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
        assert self.params.has_key( name ), 'option "%s" not found!'%name
        self.params[ name ] = value
        
    def get_params(self):
        previewImage = self.params.get("previewImage", "")
        streamName = self.params.get("streamName", self.getStreamName())
        
        hostName = self.params.get("hostName", "localhost")
        portNumber = self.params.get("portNumber", 80)
        hostDomain = "http://%s:%s"%(hostName, portNumber)
        staticUrl = hostDomain + "/static"
        
        autostart = str(self.params["autostart"]).lower()
        skinName = self.skins.get(self.params["skinName"], self.defaultSkin)
        
        swfStreamPlugin = staticUrl + "/flowplayer/plugins/flowplayer.pseudostreaming-3.2.11.swf"
        controlSkin = staticUrl+ "/flowplayer/skins/" + skinName
        
        swfPlayer = staticUrl+ "/flowplayer/" + self.swf_players[0]
        streamFile = hostDomain + "/" + streamName
        self.swf_players.reverse()
        
        params = {
            "hostDomain": hostDomain,
            "file": streamFile,
            "swfPlayer": swfPlayer,
            "swfStreamPlugin": swfStreamPlugin,
            "allowscriptaccess": "always", 
            "http.startparam": "start",	
            "allowfullscreen": "true", 
            "image": previewImage,
            "autoPlay": autostart,
            "provider": "pseudo",
            "controlSkin": controlSkin,
        }
        return params
    
    def reload(self):
        """ recarrega a página, atualizando seu conteúdo """
        fullpage = self.getPlayerPage( self.get_params() )
        self.webview.SetPage(fullpage, "Loader")
        self.webview.Reload()
        
########################################################################################
if __name__=='__main__':
    app = wx.App( 0 )
    frame = wx.Frame(None, -1, "Player", size = (700, 480))
    iewindow = Player( frame)
    frame.Show()
    app.MainLoop()