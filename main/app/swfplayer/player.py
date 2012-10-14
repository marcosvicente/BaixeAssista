# -*- coding: ISO-8859-1 -*-

import os
import wx
import string
import random
import wx.html2 as Webview
from main import settings
from django.template import Context, Template, loader
########################################################################

class Player(wx.Panel):
    # template usando na renderiza��o do player
    template = ""
    # nome da skin padr�o usanda no playe
    defaultskin = ""
    # nome, base, do diret�rio do player
    filesdirname = ""
    # caminho, completo do diret�rio de arquivos do player
    filesdir = ""
    # caminho completo para o diret�rios de skin do player
    skinsdir = ""
    # arquivos swfs
    swf_players = []
    
    def __init__(self, parent, **params):
        """params = {}
        previewImage: local da imagem mostrada no backgroud do player.
        streamName: nome da stream de video sendo transferida.
        hostName: 
        portNumber:
        """
        wx.Panel.__init__(self, parent, style=0)
        self.params = params
        self.skins = {}
        
        # defaut params
        if not params.has_key("hostName"):
            self.params["hostName"] = "localhost"
            
        if not params.has_key("portNumber"):
            self.params["portNumber"] = 8002
            
        if not params.has_key("autostart"):
            self.params["autostart"] = False
        
        try:
            skins = os.listdir( self.skinsdir )
            for filename in skins:
                name = os.path.splitext(filename)[0]
                self.skins[ name ] = filename
        except: # skin usada no primeiro carregamento.
            self.skins[ self.defaultskin ] = self.defaultskin+".swf"
        
        if not params.has_key("skinName") or not self.hasSkinName(params["skinName"]):
            self.params["skinName"] = self.defaultskin
            
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.webview = Webview.WebView.New(self)
        
        self.Bind(Webview.EVT_WEB_VIEW_NAVIGATING, self.OnWebViewNavigating, self.webview)
        sizer.Add(self.webview, 1, wx.EXPAND)
        
        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        
    @classmethod
    def getPlayerPage(cls, params):
        tmpl_dir = os.path.join(settings.APPDIR, "templates")
        try: tmpl = loader.find_template(cls.template, dirs=(tmpl_dir,))[0]
        except: tmpl = loader.get_template(os.path.join(tmpl_dir, cls.template))
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
    
    def hasSkinName(self, name):
        return self.skins.has_key(name)
        
    def getStreamName(self, size=25):
        letras = [char for char in string.ascii_letters]
        filename = "".join( [random.choice( letras) for i in range(size)] )
        return filename
    
    def __setitem__(self, name, value):
        assert self.params.has_key( name ), 'set:option "%s" not found!'%name
        self.params[ name ] = value
        
    def __getitem__(self, name):
        assert self.params.has_key( name ), 'get:option "%s" not found!'%name
        return self.params[ name ]
    
    def pause(self):
        """ pausa a execu��o do video """
        self.webview.RunScript("BA_GLOBAL_PLAYER.pause();")
        
    def getParams(self):
        previmage = self.params.get("previewImage", "")
        streamname = self.params.get("streamName", self.getStreamName(5))
        
        hostname = self.params.get("hostName", "localhost")
        portnumber = self.params.get("portNumber", 8002)
        
        domain = "http://%s:%s"%(hostname, portnumber)
        static = domain + settings.STATIC_URL.rstrip("/")
        
        skinname = self.skins.get(self.params["skinName"], self.defaultskin)
        skin = "/".join([static, self.filesdirname, "skins", skinname])
        
        swfplayer = "/".join([static, self.filesdirname, self.swf_players[0]])
        autostart = str(self.params["autostart"]).lower()
        streamfile = domain + "/stream/" + streamname
        
        self.swf_players.reverse()
        
        params = {
            "staticurl": static,
            "hostdomain": domain,
            "file": streamfile,
            "swfplayer": swfplayer,
            "allowscriptaccess": "always",   
            "allowfullscreen": "true",
            "http_startparam": "start",
            "image": previmage,
            "autostart": autostart,
            "provider": "pseudo",
            "skin": skin,
        }
        return params
    
    def reload(self):
        """ recarrega a p�gina atualizando os par�metros do player """
        params = self.getParams()
        fullpage = self.getPlayerPage( params )
        self.webview.SetPage(fullpage, params["file"])
        self.webview.Reload()
        
########################################################################################
if __name__=='__main__':
    app = wx.App( 0 )
    frame = wx.Frame(None, -1, "Player", size = (700, 480))
    iewindow = Player( frame)
    frame.Show()
    app.MainLoop()