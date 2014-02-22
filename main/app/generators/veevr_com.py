# coding: utf-8
import xml
import re
import urllib.parse

from ._sitebase import SiteBase
from main.app.util import sites


class Veevr(SiteBase):
    ## http://veevr.com/videos/L5pP6wxDK
    controller = {
        "url": "http://veevr.com/videos/%s",
        "patterns": re.compile("(?P<inner_url>(?:http://)?veevr\.com/videos/(?P<id>\w+))"),
        "control": "SM_RANGE",
        "video_control": None
    }

    def __init__(self, url, **params):
        """Constructor"""
        SiteBase.__init__(self, **params)
        self.basename = "veevr.com"
        self.url = url

    def start_extraction(self, proxies={}, timeout=25):
        # p�gina web inicial
        fd = self.connect(self.url, proxies=proxies, timeout=timeout)
        web_page = fd.read()
        fd.close()

        try:
            patternUrl = "http://mps.hwcdn.net/.+?/ads/videos/download.+?"
            matchobj = re.search(
                "playlist:.+?url:\s*(?:'|\")(%s)(?:'|\")" % patternUrl,
                web_page, re.DOTALL | re.IGNORECASE
            )
            # url final para o vídeo ?
            media_url = urllib.parse.unquote_plus(matchobj.group(1))
        except Exception as e:
            matchobj = re.search(
                "playlist:.+url:\s*(?:'|\")(http://hwcdn.net/.+/cds/.+?token=.+?)(?:'|\")",
                web_page, re.DOTALL | re.IGNORECASE)

            # url final para o v�deo
            media_url = matchobj.group(1)
            media_url = urllib.parse.unquote_plus(media_url)

        # iniciando a extra��o do t�tulo do v�deo
        try:
            matchobj = re.search("property=\"og:title\" content=\"(.+?)\"", web_page)
            title = matchobj.group(1)
        except:
            try:
                matchobj = re.search("property=\"og:description\" content=\"(.+?)\"", web_page)
                title = matchobj.group(1)[:25]  # apenas parte da descri��o ser� usada
            except:
                # usa um titulo gerado de caracteres aleat�rios
                title = sites.get_random_text()

        ext = "mp4"

        if re.match(".+/Manifest\.", media_url):
            fd = self.connect(media_url, proxies=proxies, timeout=timeout)
            xml_data = fd.read()
            fd.close()

            # documento xml
            doc = xml.etree.ElementTree.fromstring(xml_data)

            # url final para o v�deo
            media = doc.find("{http://ns.adobe.com/f4m/1.0}media")
            media_url = media.attrib["url"] + "Seg1-Frag1"

            try:
                mime_type = doc.find("{http://ns.adobe.com/f4m/1.0}mimeType")
                ext = mime_type.text.split("/", 1)[-1]  # extens�o representada pelo texto da tag
            except:
                pass

        self.configs = {"url": media_url, "ext": ext, "title": title}