# coding: utf-8
from _sitebase import *

######################################## VEEVR ########################################
class Veevr( SiteBase ):
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
        webpage = fd.read(); fd.close()
        
        try:
            patternUrl = "http://mps.hwcdn.net/.+?/ads/videos/download.+?"
            matchobj = re.search(
                "playlist:.+?url:\s*(?:'|\")(%s)(?:'|\")"%patternUrl, 
                webpage, re.DOTALL|re.IGNORECASE
            )
            # url final para o v�deo ?
            mediaUrl = urllib.unquote_plus( matchobj.group(1) )
        except Exception as err:
            matchobj = re.search(
                "playlist:.+url:\s*(?:'|\")(http://hwcdn.net/.+/cds/.+?token=.+?)(?:'|\")", 
                webpage, re.DOTALL|re.IGNORECASE )

            # url final para o v�deo
            mediaUrl = matchobj.group(1)
            mediaUrl = urllib.unquote_plus( mediaUrl )

        # iniciando a extra��o do t�tulo do v�deo
        try:
            matchobj = re.search("property=\"og:title\" content=\"(.+?)\"", webpage)
            title = matchobj.group(1)
        except:
            try:
                matchobj = re.search("property=\"og:description\" content=\"(.+?)\"", webpage)
                title = matchobj.group(1)[:25] # apenas parte da descri��o ser� usada                            
            except:
                # usa um titulo gerado de caracteres aleat�rios
                title = sites.get_random_text()

        ext = "mp4" # extens�o padr�o

        if re.match(".+/Manifest\.", mediaUrl):
            fd = self.connect(mediaUrl, proxies=proxies, timeout=timeout)
            xmlData = fd.read(); fd.close()

            # documento xml
            mdoc = xml.etree.ElementTree.fromstring( xmlData )

            # url final para o v�deo
            media = mdoc.find("{http://ns.adobe.com/f4m/1.0}media")
            mediaUrl = media.attrib["url"] + "Seg1-Frag1"

            try:
                mimeType = mdoc.find("{http://ns.adobe.com/f4m/1.0}mimeType")
                ext = mimeType.text.split("/", 1)[-1] # extens�o representada pelo texto da tag
            except:pass # em caso de erro, usa a extes�o padr�o

        self.configs = {"url": mediaUrl, "ext": ext, "title": title}