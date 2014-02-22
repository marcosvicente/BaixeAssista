# -*- coding: ISO-8859-1 -*-

import os
from PySide import QtCore, QtGui, QtWebKit
from django.template import Context, Template, loader
from django.core.urlresolvers import reverse
from main.app.util.sites import get_random_text
from main.app.manager.server import Server
from main import settings
import urllib.request, urllib.parse, urllib.error

## --------------------------------------------------------------------

class Player(QtGui.QWidget):
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
    flashplayer = ""
    
    relativeurl = reverse("player-loader")
    
    def __init__(self, parent=None, **params):
        """params = {}
        previewImage: local da imagem mostrada no backgroud do player.
        streamName: nome da stream de video sendo transferida.
        hostName: 
        portNumber:
        """
        super(Player, self).__init__(parent)
        self.params = params
        self.skins = {}
        
        # defaut params
        params.setdefault("hostName", Server.HOST)
        params.setdefault("portNumber", Server.PORT)
        params.setdefault("skinName", self.defaultskin)
        params.setdefault("autostart", False)
        
        try:
            for filename in os.listdir( self.skinsdir ):
                name = os.path.splitext(filename)[0]
                self.skins[ name ] = filename
        except: # skin usada no primeiro carregamento.
            self.skins[ self.defaultskin ] = self.defaultskin+".swf"
        
        if not self.hasSkinName( params["skinName"] ):
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
        return list(self.skins.keys())
    
    def hasSkinName(self, name):
        return name in self.skins
    
    def __setitem__(self, name, value):
        assert name in self.params, 'set:option "%s" not found!'%name
        self.params[ name ] = value
        
    def __getitem__(self, name):
        assert name in self.params, 'get:option "%s" not found!'%name
        return self.params[ name ]
    
    def stop(self):
        self.webview.setHtml("")
    
    def update(self, **kwargs):
        """ atualiza 'params' mas passa pela validação """
        for key, value in list(kwargs.items()):
            self[key] = value
            
    def pause(self):
        """ pausa a execução do video """
        frame = self.webview.page().mainFrame()
        frame.evaluateJavaScript("BA_GLOBAL_PLAYER.stop();")
    
    def getParams(self):
        previmage = self.params.get("previewImage", "")
        streamname = self.params.get("streamName", get_random_text(5)+".flv")
        
        hostname = self.params.get("hostName", Server.HOST)
        portnumber = self.params.get("portNumber", Server.PORT)
        
        domain = "http://%s:%s"%(hostname, portnumber)
        static = settings.STATIC_URL.rstrip("/")
        
        jqueryscript = "/".join([static, "js", "jquery-1.8.2.min.js"])
        jsonscript = "/".join([static, "js", "json2.js"])
        playerscript = "/".join([static, self.filesdirname, "js", self.playerapi])
        
        skinname = self.skins.get(self.params["skinName"], self.defaultskin)
        skin = "/".join([static, self.filesdirname, "skins", skinname])
        
        swfplayer = "/".join([static, self.filesdirname, self.flashplayer])
        autostart = str(self.params["autostart"]).lower()
        streamfile = "/".join(["/stream", streamname])
        
        params = {
            "static": static,
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
        params["template"] = self.template
        fullurl = params["hostdomain"] + self.relativeurl+"?"+urllib.parse.urlencode(params)
        self.webview.load( fullurl )
        
        
        
        