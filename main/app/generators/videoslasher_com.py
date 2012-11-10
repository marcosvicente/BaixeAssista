# coding: utf-8
from putlocker_com import *

########################################################################
class Videoslasher( SiteBase ):
    ##<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">
    ##<channel><item><title>Preview</title>
    ##<media:content url="http://www.videoslasher.com/static/img/previews/3/37/370f254c0be38819213191232e528d78.jpg" type="image/jpeg">
    ##</media:content></item><item><title>Video</title><link>http://www.videoslasher.com/video/6O9TSHUUR4UY</link>
    ##<media:content url="http://proxy1.videoslasher.com/free/6/6O/6O9TSHUUR4UY.flv?h=ih4mBk-jPyXCEJ-aaDaY3g&e=1344819603" type="video/x-flv"  duration="5269" />
    ##</item></channel></rss>
    
    ## http://www.videoslasher.com/video/6O9TSHUUR4UY == http://www.videoslasher.com/embed/6O9TSHUUR4UY
    controller = {
        "url": "http://www.videoslasher.com/video/%s", 
        "patterns": (
            re.compile("(?P<inner_url>http://www\.videoslasher\.com/video/(?P<id>\w+))"),
            [re.compile("(?P<inner_url>http://www\.videoslasher\.com/embed/(?P<id>\w+))")]
        ),
        "control": "SM_SEEK",
        "video_control": None
    }
    domain =  "http://www.videoslasher.com"
    #----------------------------------------------------------------------
    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "videoslasher.com"
        self.url = url
    
    def suportaSeekBar(self):
        return True
    
    def postPage(self, webpage, proxies, timeout):
        matchobj = PutLocker.patternForm.search( webpage )
        hashvalue =  matchobj.group("hash") or  matchobj.group("_hash")
        hashname = matchobj.group("name") or  matchobj.group("_name")
        confirmvalue = matchobj.group("confirm")
        
        data = urllib.urlencode({hashname: hashvalue, "confirm": confirmvalue})
        fd = self.connect(self.url, proxies=proxies, timeout=timeout, data=data)
        webpage = fd.read(); fd.close()
        return webpage
    
    def start_extraction(self, proxies={}, timeout=25):
        fd = self.connect(self.url, proxies=proxies, timeout=timeout)
        firstWebpage = fd.read(); fd.close()
        
        try: webpage = self.postPage(firstWebpage, proxies, timeout)
        except: webpage = firstWebpage
        
        matchobj = re.search("""playlist:\s*(?:'|")(/playlist/\w+)(?:'|")""", webpage, re.DOTALL)
        playlistUrl = matchobj.group(1)
        
        if not playlistUrl.endswith('/'):
            playlistUrl += '/'
        
        fd = self.connect(self.domain + playlistUrl, proxies=proxies, timeout=timeout)
        rssData = fd.read(); fd.close()
        
        for item in re.findall("<item>(.+?)</item>", rssData, re.DOTALL):
            matchobj = re.search('''\<media:content\s*url\s*=\s*"(.+?)"\s*type="video.+?"''', item, re.DOTALL)
            if matchobj:
                url = matchobj.group(1)
                break
        else:
            raise Exception
        
        try: title = re.search("<title>(.+?)</title>", webpage, re.DOTALL).group(1)
        except: title = sites.get_random_text()
        
        self.configs = {"url": url+"&start=", "title": title}