# coding: utf-8
from _sitebase import *

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
    
    def __init__(self, url, **params):
        """Constructor"""
        SiteBase.__init__(self, **params)
        self.info_url = "http://www.youtube.com/get_video_info?video_id=%s&el=embedded&ps=default&eurl=&hl=en_US"
        self.video_quality_opts = {1: "small", 2: "medium", 3: "large"}
        self.basename = u"youtube.com"
        self.raw_data = None
        self.url = url
        
    def suportaSeekBar(self):
        return True
    
    def getMessage(self):
        try:
            if self.raw_data.get("status",[""])[0] == "fail":
                reason = self.raw_data.get("reason",[""])[0]
                msg = u"%s informa: %s"%(self.basename, unicode(reason,"UTF-8"))
            else: msg = ""
        except: msg = ""
        return msg
    
    def getLink(self):
        vquality = self.params.get("qualidade", 2)
        quality_opt = self.video_quality_opts[ vquality ]
        
        quality_size = len(self.raw_data['quality'])
        type_size    = len(self.raw_data["type"])
        url_size     = len(self.configs["urls"])
        
        if quality_size == type_size == url_size:
            items = zip(self.configs["urls"], self.raw_data["type"], 
                        self.raw_data['quality'])
            
            def link( args ):
                url, _type, quality = args
                
                matchobj = re.search("video/([^\s;]+)", _type)
                if matchobj: self.configs["ext"] = matchobj.group(1)
                
                if re.match(quality_opt, quality):
                    return urllib.unquote_plus( url )
            
            result = filter(link, items)
            result = result if len(result) > 0 else items
            return result[0][0] + "&range=%s-"
        else:
            items = zip(self.configs["urls"], self.raw_data["type"])
            
            def link( args ):
                url, _type = args
                
                matchobj = re.search("video/([^\s;]+)", _type)
                if matchobj: self.configs["ext"] = matchobj.group(1)
                
                if re.search(quality_opt, _type):
                    return urllib.unquote_plus( url )
                
            result = filter(link, items)
            result = result if len(result) > 0 else items
            return result[0][0] + "&range=%s-"
        
    def get_raw_data(self, proxies, timeout):
        video_id = Universal.get_video_id(self.basename, self.url)
        url = self.info_url % video_id
        fd = self.connect(url, proxies=proxies, timeout=timeout)
        data = fd.read(); fd.close()
        return cgi.parse_qs( data )
    
    def start_extraction(self, proxies={}, timeout=25):
        self.raw_data = self.get_raw_data(proxies, timeout)
        self.message = self.getMessage()
        
        uparams = cgi.parse_qs(self.raw_data["url_encoded_fmt_stream_map"][0])
        
        self.raw_data["quality"] = uparams["quality"]
        self.raw_data["type"] = uparams["type"]
        self.configs["urls"] = []
        
        for index, url in enumerate(uparams["url"]):
            fullurl = url + "&signature=%s" %uparams["sig"][index]
            self.configs["urls"].append( fullurl )
            
        try: self.configs["title"] = self.raw_data["title"][0]
        except (KeyError, IndexError):
            self.configs["title"] = sites.get_random_text()
            
        try: self.configs["thumbnail_url"] = self.raw_data["thumbnail_url"][0]
        except (KeyError, IndexError):
            self.configs["thumbnail_url"] = ""
            
            
            