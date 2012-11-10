# coding: utf-8
from _sitebase import *

###################################### REDTUBE #######################################
class Redtube( SiteBase ):
    ## http://www.redtube.com/78790
    controller = {
        "url": "http://www.redtube.com/%s", 
        "patterns": re.compile("(?P<inner_url>http://www.redtube.com/(?P<id>\d+))"),
        "control": "SM_SEEK",
        "video_control": None
    }

    def __init__(self, url, **params):
        """Constructor"""
        SiteBase.__init__(self, **params)
        self.basename = "redtube.com"
        self.url = url

    def suportaSeekBar(self): return True
    
    def start_extraction(self, proxies={}, timeout=25):
        fd = self.connect(self.url, proxies=proxies, timeout=timeout)
        webpage = fd.read(); fd.close()
        
        flashvar = re.search("""so\.addParam\((?:"|')flashvars(?:"|'),\s*(?:"|')(.*?)(?:"|')""", webpage).group(1)
        video_data = cgi.parse_qs(flashvar)

        try: title = re.search("<title>(.*?)</title>", webpage).group(1)
        except: title = sites.get_random_text()
        
        self.configs = {"url": video_data["flv_h264_url"][0]+"&ec_seek=", "title": title}