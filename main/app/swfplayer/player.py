# -*- coding: ISO-8859-1 -*-

import os
import wx
import string
import random
import wx.html2 as Webview
from main import settings
from django.template import Context, Template, loader,
from main.app.util.sites import get_random_text 
import json
########################################################################

class Player(wx.Panel):
    # template usando na renderização do player
    template = ""
    # nome da skin padrão usanda no playe
    defaultskin = ""
    # nome, base, do diretório do player
    filesdirname = ""
    # script que fará o carregamento do player, expondo seu dados e atributos.
    playerapi = ""
    # caminho, completo do diretório de arquivos do player
    filesdir = ""
    # caminho completo para o diretórios de skin do player
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
        self.json_data = {}
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
        self.Bind(Webview.EVT_WEB_VIEW_TITLE_CHANGED, self.InterfaceJson, self.webview)
        sizer.Add(self.webview, 1, wx.EXPAND)
        
        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        
    @classmethod
    def getPlayerPage(cls, params):
        try: tmpl = loader.get_template(cls.template)
        except: tmpl = loader.find_template(cls.template, dirs=(settings.TEMPLATE_PATH,))[0]
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
    
    def __setitem__(self, name, value):
        assert self.params.has_key( name ), 'set:option "%s" not found!'%name
        self.params[ name ] = value
        
    def __getitem__(self, name):
        assert self.params.has_key( name ), 'get:option "%s" not found!'%name
        return self.params[ name ]
    
    def pause(self):
        """ pausa a execução do video """
        self.webview.RunScript("BA_GLOBAL_PLAYER.stop();")
    
    def get_json(self, name, default=None):
        return self.json_data.get(name, default)
    
    def InterfaceJson(self, event):
        data = self.webview.GetCurrentTitle()
        try: self.json_data.update(json.loads(data))
        except: pass
    
    def getParams(self):
        previmage = self.params.get("previewImage", "")
        streamname = self.params.get("streamName", get_random_text(5))
        
        hostname = self.params.get("hostName", "localhost")
        portnumber = self.params.get("portNumber", 8002)
        
        domain = "http://%s:%s"%(hostname, portnumber)
        static = domain + settings.STATIC_URL.rstrip("/")
        
        jqueryscript = "/".join([static, "js", "jquery-1.8.2.min.js"])
        jsonscript = "/".join([static, "js", "json2.js"])
        playerscript = "/".join([static, self.filesdirname, "js", self.playerapi])
        
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
            "jqueryscript": jqueryscript,
            "jsonscript": jsonscript,
            "playerscript": playerscript,
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
        """ recarrega a página atualizando os parâmetros do player """
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