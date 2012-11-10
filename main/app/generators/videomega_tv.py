from _sitebase import *

###################################### MEGAVIDEO ######################################
class Videomega( SiteBase ):
    ## http://videomega.tv/iframe.php?ref=OEKgdSTMGQ&width=505&height=4
    controller = {
        "url": "http://videomega.tv/iframe.php?ref=%s", 
        "patterns": [re.compile("(?P<inner_url>http://videomega\.tv/iframe\.php\?ref=(?P<id>\w+)(?:&width=\d+)?(&height=\d+)?)")], 
        "control": "SM_RANGE", 
        "video_control": None
    }
    
    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.url = url
        
    def suportaSeekBar(self):
        return True
    
    def start_extraction(self, proxies={}, timeout=25):
        fd = self.connect(self.url, proxies=proxies, timeout=timeout)    
        webpage = fd.read(); fd.close()
        
        matchobj = re.search("unescape\s*\((?:\"|')(.+)(?:\"|')\)", webpage)
        settings = urllib.unquote_plus( matchobj.group(1) )
        
        matchobj = re.search("file\s*:\s*(?:\"|')(.+?)(?:\"|')", settings)
        url = matchobj.group(1)
        
        try: title = re.search("<title>(.+)</title>", webpage).group(1)
        except: title = get_radom_title()
        
        self.configs = {"url": url+"&start=", "title": title}