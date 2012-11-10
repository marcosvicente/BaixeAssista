from _sitebase import *

###################################### XVIDEOS #######################################
class Xvideos( SiteBase ):
    ## http://www.xvideos.com/video2037621/mommy_and_daughter_spreading
    controller = {
        "url": "http://www.xvideos.com/%s", 
        "patterns": re.compile("(?P<inner_url>http://www.xvideos.com/(?P<id>video\w+)(?:/\w+)?)"),
        "control": "SM_SEEK",
        "video_control": None
    }
    
    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "xvideos.com"
        self.url = url
    
    def suportaSeekBar(self): return True
    
    def start_extraction(self, proxies={}, timeout=25):
        fd = self.connect(self.url, proxies=proxies, timeout=timeout)
        webpage = fd.read(); fd.close()
        
        flashvar = re.search('\<embed\s*type.+flashvars="(.*?)"', webpage).group(1)
        video_data = cgi.parse_qs(flashvar)

        try: title = re.search("<title>(.*?)</title>", webpage).group(1)
        except: title = get_radom_title()

        self.configs = {"url": video_data["flv_url"][0]+"&fs=", "title": title}
        