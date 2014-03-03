# coding: utf-8
import xml
import re
import urllib.parse

from ._sitebase import SiteBase
from main.app.util import sites


class Veevr(SiteBase):
    ##
    # http://veevr.com/videos/L5pP6wxDK
    ##
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
        request = self.connect(self.url, proxies=proxies, timeout=timeout)
        page = request.text
        request.close()

        try:
            p_url = "http://mps.hwcdn.net/.+?/ads/videos/download.+?"
            match_obj = re.search(
                "playlist:.+?url:\s*(?:'|\")(%s)(?:'|\")" % p_url, page,
                re.DOTALL | re.IGNORECASE
            )
            # url final para o vídeo ?
            media_url = urllib.parse.unquote_plus(match_obj.group(1))
        except Exception:
            match_obj = re.search(
                "playlist:.+url:\s*(?:'|\")(http://hwcdn.net/.+/cds/.+?token=.+?)(?:'|\")", page,
                re.DOTALL | re.IGNORECASE
            )
            # url final para o vídeo
            media_url = match_obj.group(1)
            media_url = urllib.parse.unquote_plus(media_url)

        try:
            match_obj = re.search("property=\"og:title\" content=\"(.+?)\"", page)
            title = match_obj.group(1)
        except:
            try:
                match_obj = re.search("property=\"og:description\" content=\"(.+?)\"", page)
                title = match_obj.group(1)[:25]
            except:
                title = sites.get_random_text()
        ext = "mp4"

        if re.match(".+/Manifest\.", media_url):
            request = self.connect(media_url, proxies=proxies, timeout=timeout)
            xml_data = request.text
            request.close()

            # documento xml
            doc = xml.etree.ElementTree.fromstring(xml_data)

            # url final para o vídeo
            media = doc.find("{http://ns.adobe.com/f4m/1.0}media")
            media_url = media.attrib["url"] + "Seg1-Frag1"

            try:
                mime_type = doc.find("{http://ns.adobe.com/f4m/1.0}mimeType")
                ext = mime_type.text.split("/", 1)[-1]
            except:
                pass

        self.configs = {
            "url": media_url,
            "ext": ext,
            "title": title
        }