# -*- coding: ISO-8859-1 -*-

import os, json
from PySide import QtCore, QtGui, QtWebKit
from main import settings
from django.template import Context, Template, loader
from main.app.util.sites import get_random_text


class Player(QtGui.QWidget):
    # template usando na renderiza��o do player
    template = ""
    # nome da skin padr�o usanda no playe
    defaultskin = ""
    # nome, base, do diret�rio do player
    filesdirname = ""
    # script que far� o carregamento do player, expondo seu dados e atributos.
    playerapi = ""
    # caminho, completo do diret�rio de arquivos do player
    filesdir = ""
    # caminho completo para o diret�rios de skin do player
    skinsdir = ""
    # arquivos swfs
    swf_players = []
    
    def __init__(self, parent=None, **params):
        """params = {}
        previewImage: local da imagem mostrada no backgroud do player.
        streamName: nome da stream de video sendo transferida.
        hostName: 
        portNumber:
        """
        super(Player, self).__init__(parent)
        self.json_data = {}
        self.params = params
        self.skins = {}
        
        # defaut params
        params.setdefault("hostName", "localhost")
        params.setdefault("portNumber", 8002)
        params.setdefault("autostart", False)
        
        try:
            skins = os.listdir( self.skinsdir )
            for filename in skins:
                name = os.path.splitext(filename)[0]
                self.skins[ name ] = filename
        except: # skin usada no primeiro carregamento.
            self.skins[ self.defaultskin ] = self.defaultskin+".swf"
        
        if not params.has_key("skinName") or not self.hasSkinName(params["skinName"]):
            self.params["skinName"] = self.defaultskin
            
        self.webview = QtWebKit.QWebView(self)
        self.webview.settings().setAttribute(QtWebKit.QWebSettings.PluginsEnabled, True)
        
        vBox = QtGui.QVBoxLayout()
        vBox.addWidget( self.webview )
        
        self.setLayout( vBox )
        
    @classmethod
    def getPlayerPage(cls, params):
        try: tmpl = loader.get_template(cls.template)
        except: tmpl = loader.find_template(cls.template, dirs=(settings.TEMPLATE_PATH,))[0]
        return tmpl.render(Context({"params": params}))
        
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
        """ pausa a execu��o do video """
        frame = self.webview.page().mainFrame()
        frame.evaluateJavaScript("BA_GLOBAL_PLAYER.stop();")
        
    def get_json(self, name, default=None):
        return self.json_data.get(name, default)
    
    def InterfaceJson(self, event):
        data = self.webview.GetCurrentTitle()
        try: self.json_data.update(json.loads(data))
        except: pass
    
    def getParams(self):
        previmage = self.params.get("previewImage", "")
        streamname = self.params.get("streamName", get_random_text(5)+".flv")
        
        hostname = self.params.get("hostName", "localhost")
        portnumber = self.params.get("portNumber", 8002)
        
        domain = "http://%s:%s"%(hostname, portnumber)
        static = (domain + settings.STATIC_URL).strip("/")
        
        jqueryscript = "/".join([static, "js", "jquery-1.8.2.min.js"])
        jsonscript = "/".join([static, "js", "json2.js"])
        playerscript = "/".join([static, self.filesdirname, "js", self.playerapi])
        
        skinname = self.skins.get(self.params["skinName"], self.defaultskin)
        skin = "/".join([static, self.filesdirname, "skins", skinname])
        
        swfplayer = "/".join([static, self.filesdirname, self.swf_players[0]])
        autostart = str(self.params["autostart"]).lower()
        streamfile = "/".join([domain, "stream", streamname])
        
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
        """ recarrega a p�gina atualizando os par�metros do player """
        params = self.getParams()
        html = self.getPlayerPage( params )
        
        #print html
        
        self.webview.setHtml(html)
        self.webview.reload()
        