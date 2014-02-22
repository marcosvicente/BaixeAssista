# coding: utf-8
from ._sitebase import *

########################################################################
class FlashxTv( SiteBase ):
    ## http://play.flashx.tv/nuevo/player/cst.php?hash=1AB71XOUKW77
    ## http://flashx.tv/video/18U57YS4698X/REM-Blue
    ## http://play.flashx.tv/player/embed.php?hash=1AB71XOUKW77
    ## http://play.flashx.tv/player/embed.php?vid=401804&width=620&height=400&autoplay=no
    controller = {
        "url": "http://flashx.tv/video/%s",
        "basenames": ["play.flashx", "flashx.tv"],
        "patterns": (
             re.compile("(?P<inner_url>http://flashx\.tv/video/(?P<id>\w+)/(?:\w+)?)"),
            [re.compile("(?P<inner_url>http://play\.flashx\.tv/player/embed\.php\?(?:hash|vid)=(?P<id>\w+))")],
        ),
        "control": "SM_SEEK",
        "video_control": None
    }
    xmlLink = "http://play.flashx.tv/nuevo/player/cst.php?hash=%s"
    #----------------------------------------------------------------------
    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "flashx.tv"
        self.url = url
    
    def suportaSeekBar(self):
        return True
    
    def start_extraction(self, proxies={}, timeout=25):
        if Universal.isEmbed(self.url) and re.match(".+embed\.php\?vid=", self.url):
            fd = self.connect(self.url, proxies=proxies, timeout=timeout)
            webPage = fd.read(); fd.close()
            video_id = re.search("hash=(\w+)&", webPage, re.DOTALL).group(1)
        else:
            video_id = Universal.get_video_id(self.basename, self.url)
            webPage = None
            
        fd = self.connect(self.xmlLink % video_id, proxies=proxies, timeout=timeout)
        xmlData = fd.read(); fd.close()
        
        matchobj = re.search("<file>(.+)</file>", xmlData, re.DOTALL)
        url = matchobj.group(1)
        
        try: httpparam = "?%s=" % re.search("<httpparam>(.+)</httpparam>", xmlData, re.DOTALL).group(1)
        except: httpparam = "?start="
        
        if webPage is None:
            try: title = os.path.basename( self.url )
            except: title = sites.get_random_text()
        else:
            try: title = re.search("<title>(.+)</title>", webPage, re.DOTALL).group(1)
            except: title = sites.get_random_text()
            
        self.configs = {"url": url + httpparam, "title": title}
        
        