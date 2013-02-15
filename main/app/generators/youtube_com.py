# coding: utf-8
from main.app.generators import Universal
from main.app.util import sites
from _sitebase import SiteBase
import urllib
import cgi
import re

####################################### YOUTUBE #######################################
class Youtube( SiteBase ):
    ## normal: http://www.youtube.com/watch?v=bWDZ-od-otI
    ## embutida: http://www.youtube.com/watch?feature=player_embedded&v=_PMU_jvOS4U
    ## http://www.youtube.com/watch?v=VW51Q_YBsNk&feature=player_embedded
    ## http://www.youtube.com/v/VW51Q_YBsNk?fs=1&hl=pt_BR&rel=0&color1=0x5d1719&color2=0xcd311b
    ## http://www.youtube.com/embed/ulZZ4mG9Ums
    controller = {
        "url": "http://www.youtube.com/watch?v=%s", 
        "patterns": (
             re.compile("(?P<inner_url>(?:https?://)?www\.youtube\.com/watch\?.*v=(?P<id>[0-9A-Za-z_-]+))"),
            [re.compile("(?P<inner_url>(?:https?://)?www.youtube(?:-nocookie)?\.com/(?:v/|embed/)(?P<id>[0-9A-Za-z_-]+))")]
        ), 
        "control": "SM_SEEK", 
        "video_control": None
    }
    
    info_url = "http://www.youtube.com/get_video_info?video_id=%s&el=embedded&ps=default&eurl=&hl=en_US"
    video_quality_opts = {1: "small", 2: "medium", 3: "large"}
    
    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = u"youtube.com"
        self.video_info = {}
        self.url = url
        
    def suportaSeekBar(self): return True
    def getFailReason(self):
        try:
            if self.raw_data["status"] == "fail":
                reason = self.raw_data["reason"].decode("utf-8")
                reason = u"%s informa: %s" % (self.basename, reason)
            else: reason = u""
        except: reason = u""
        return reason
        
    def getLink(self):
        quality = self.params.get("qualidade", 2)
        quality = self.video_quality_opts[quality]
        pattern_type = re.compile("video/(?P<type>[^\s;]+)")
        
        for video_info in self.video_info:
            if video_info["quality"].endswith( quality ):
                url = video_info["url"]
                
                matchobj = pattern_type.search(video_info["type"])
                self.configs["ext"] = matchobj.group("type")
                break
        return url
    
    def extract_one(self):
        """ método de extração padrão. funciona na maioria das vezes """
        stream_map = self.raw_data["url_encoded_fmt_stream_map"]
        
        def parse_qs(item):
            """ analizando os dados e removendo os indices """
            data = cgi.parse_qs(item)
            
            for key in data.iterkeys():
                data[key] = data[key][0]
                
            data["url"] = urllib.unquote_plus(data["url"])
            data["url"] = "&".join([data["url"], "signature=%s" % data["sig"], "range=%s-"])
            return data
        
        return map(parse_qs, stream_map.split(","))
    
    def start_extraction(self, proxies={}, timeout=25):
        url = self.info_url % Universal.get_video_id(self.basename, self.url)
        fd = self.connect(url, proxies=proxies, timeout=timeout)
        self.raw_data = cgi.parse_qs(fd.read()); fd.close()
        
        for key in self.raw_data.iterkeys(): # index remove
            self.raw_data[key] = self.raw_data[key][0]
            
        self.message = self.getFailReason()
        self.video_info = self.extract_one()
        
        try: self.configs["title"] = self.raw_data["title"]
        except (KeyError, IndexError):
            self.configs["title"] = sites.get_random_text()
            
        try: self.configs["thumbnail_url"] = self.raw_data["thumbnail_url"]
        except (KeyError, IndexError):
            self.configs["thumbnail_url"] = ""
            
            
            