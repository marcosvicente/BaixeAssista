from _sitebase import *

###################################### VK #######################################
class Vk( SiteBase ):
    ## http://vk.com/video_ext.php?oid=164478778&id=163752296&hash=246b8447ed557240&hd=1
    ## http://vk.com/video103395638_162309869?hash=23aa2195ccec043b
    controller = {
        "url": "http://vk.com/video_ext.php?%s",
        "patterns": (
             re.compile("(?P<inner_url>http://vk\.com/(?P<id>video\d+_\d+\?hash=\w+))"),
            [re.compile("(?P<inner_url>http://vk\.com/video_ext\.php\?(?P<id>oid=\w+&id=\w+&hash=\w+(?:&hd=\d+)?))")]
        ),
        "control": "SM_RANGE",
        "video_control": None
    }

    def __init__(self, url, **params):
        """Constructor"""
        SiteBase.__init__(self, **params)
        self.basename = "vk.com"
        self.url = url
        
    def suportaSeekBar(self):
        return True
    
    def getLink(self):
        vquality = int(self.params.get("qualidade", 2))
        
        optToNotFound = self.configs.get(1, None)
        optToNotFound = self.configs.get(2, optToNotFound)
        optToNotFound = self.configs.get(3, optToNotFound)
        
        videoLink = self.configs.get(vquality, optToNotFound)
        return videoLink
    
    def start_extraction(self, proxies={}, timeout=25):
        ## http://cs519609.userapi.com/u165193745/video/7cad4a848e.360.mp4
        fd = self.connect(self.url, proxies=proxies, timeout=timeout)
        webdata = fd.read(); fd.close()
        params = {}
        try:
            mathobj = re.search("var\s*video_host\s*=\s*'(?P<url>.+?)'", webdata, re.DOTALL)
            params["url"] = mathobj.group("url")
            
            mathobj = re.search("var\s*video_uid\s*=\s*'(?P<uid>.+?)'", webdata, re.DOTALL)
            params["uid"] = mathobj.group("uid")
    
            mathobj = re.search("var\s*video_vtag\s*=\s*'(?P<vtag>.+?)'", webdata, re.DOTALL)
            params["vtag"] = mathobj.group("vtag")
    
            mathobj = re.search("var\s*video_max_hd\s*=\s*(?:')?(?P<max_hd>.+?)(?:')?", webdata, re.DOTALL)
            params["max_hd"] = mathobj.group("max_hd")
    
            mathobj = re.search("var\s*video_no_flv\s*=\s*(?:')?(?P<no_flv>.+?)(?:')?", webdata, re.DOTALL)
            params["no_flv"] = mathobj.group("no_flv")
        except:
            matchobj = re.search("var\s*vars\s*=\s*{(?P<vars>.+?)}", webdata, re.DOTALL)
            raw_params = matchobj.group("vars").replace(r'\"', '"')
            params = dict([(a, (b or c)) for a,b,c in re.findall('"(.+?)"\s*:\s*(?:"(.*?)"|(-?\d*))',raw_params)])
            params["url"] = "http://cs%s.vk.com" % params.pop("host")
            
        try: title = re.search("<title>(.+?)</title>", webdata).group(1)
        except: title = get_radom_title()
        
        if int(params.get("no_flv",0)):
            baseUrl = params["url"] + "/u%s/video/%s.{res}.mp4"%(params["uid"], params["vtag"])
            url_hd240 = baseUrl.format(res = 240)
            url_hd360 = baseUrl.format(res = 360)
            ext = "mp4"
        else:
            url_hd240 = url_hd360 = params["url"] + "u%s/video/%s.flv"%(params["uid"], params["vtag"])
            ext = "flv"
            
        self.configs = {1: url_hd240, 2: url_hd360, "title": title, "ext": ext}