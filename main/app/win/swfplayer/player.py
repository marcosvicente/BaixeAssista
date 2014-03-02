# -*- coding: ISO-8859-1 -*-

import os
import urllib.request
import urllib.parse
import urllib.error

from PySide import QtWebKit
from django.template import Context, loader
from django.core.urlresolvers import reverse

from main.app.util.sites import get_random_text
from main.app.manager.server import Server
from main import settings


class Player(QtWebKit.QWebView):

    # template usando na renderização do player
    template = ''

    # nome da skin padrão usanda no playe
    skin = ''

    # nome, base, do diretório do player
    media = ''

    # script que fará o carregamento do player, expondo seu dados e atributos.
    js_api = ''

    # caminho completo do diretório de arquivos do player
    media_path = ''

    # caminho completo para o diretórios de skin do player
    skin_path = ''

    # referência para o nome do arquivo swf player
    swf_player = ''

    loader_url = reverse("player-loader")

    def __init__(self, parent=None, **params):
        """params = {}
        previewImage: local da imagem mostrada no backgroud do player.
        streamName: nome da stream de video sendo transferida.
        hostName: 
        portNumber:
        """
        super(Player, self).__init__(parent)
        self.params = params
        self.set_default_params()
        self.skins = {}
        try:
            for filename in os.listdir(self.skin_path):
                name = os.path.splitext(filename)[0]
                self.skins[name] = filename
        except:  # skin usada no primeiro carregamento.
            self.skins[self.skin] = self.skin + ".swf"

        if not self.has_skin(params["skinName"]):
            self.params["skinName"] = self.skin

        self.settings().setAttribute(QtWebKit.QWebSettings.PluginsEnabled, True)

    def set_default_params(self):
        self.params.setdefault("hostName", Server.HOST)
        self.params.setdefault("portNumber", Server.PORT)
        self.params.setdefault("skinName", self.skin)
        self.params.setdefault("autostart", False)

    @classmethod
    def get_html(cls, params):
        try:
            tmpl = loader.get_template(cls.template)
        except:
            tmpl = loader.find_template(cls.template, dirs=(settings.TEMPLATE_PATH,))[0]
        return tmpl.render(Context({"params": params}))

    def get_skins(self):
        """ retorna os nomes das skins disponiveis """
        return list(self.skins.keys())

    def has_skin(self, name):
        return name in self.skins

    def __setitem__(self, name, value):
        assert name in self.params, 'set:option "%s" not found!' % name
        self.params[name] = value

    def __getitem__(self, name):
        assert name in self.params, 'get:option "%s" not found!' % name
        return self.params[name]

    def stop(self):
        self.setHtml('')

    def update(self, **kwargs):
        """ atualiza 'params' mas passa pela validação """
        for key, value in list(kwargs.items()):
            self[key] = value

    def pause(self):
        """ pausa a execução do video """
        frame = self.webview.page().mainFrame()
        frame.evaluateJavaScript("BA_GLOBAL_PLAYER.stop();")

    def get_params(self):
        prev_image = self.params.get("previewImage", "")
        stream_name = self.params.get("streamName", get_random_text(5) + ".flv")

        hostname = self.params.get("hostName", Server.HOST)
        port = self.params.get("portNumber", Server.PORT)

        domain = "http://%s:%s" % (hostname, port)
        static = settings.STATIC_URL.rstrip("/")

        jquery = "/".join([static, "js", "jquery-1.8.2.min.js"])
        json = "/".join([static, "js", "json2.js"])
        js_api = "/".join([static, self.media, "js", self.js_api])

        skin = self.skins.get(self.params["skinName"], self.skin)
        skin = "/".join([static, self.media, "skins", skin])

        swf_player = "/".join([static, self.media, self.swf_player])
        autostart = str(self.params["autostart"]).lower()
        stream = "/".join(["/stream", stream_name])

        params = {
            "static": static,
            "hostdomain": domain,
            "file": stream,
            "jqueryscript": jquery,
            "jsonscript": json,
            "playerscript": js_api,
            "swfplayer": swf_player,
            "allowscriptaccess": "always",
            "allowfullscreen": "true",
            "http_startparam": "start",
            "image": prev_image,
            "autostart": autostart,
            "provider": "pseudo",
            "skin": skin,
        }
        return params

    def reload(self):
        """ recarrega a página atualizando os parâmetros do player """
        params = self.get_params()
        params["template"] = self.template
        url = params["hostdomain"] + self.loader_url + "?" + urllib.parse.urlencode(params)
        self.load(url)