# coding: utf-8
from _sitebase import *

###################################### MODOVIDEO ######################################
class Modovideo( SiteBase ):
    ## http://www.modovideo.com/video.php?v=08k9h2hm0mq3zjvs69850dyjpdgzghfg
    ## http://www.modovideo.com/video?v=t15yzbsacm6z10vs0wh0v9hc1cprba76
    ## http://www.modovideo.com/frame.php?v=4mcyh0h5y2gc27g2dgsc7g80j6tpw4c0
    controller = {
        "url": "http://www.modovideo.com/video.php?v=%s", 
        "patterns":(
             re.compile("(?P<inner_url>(?:http://)?(?:www\.)?modovideo\.com/(?:video\?|video\.php\?)v=(?P<id>\w+))"),
            [re.compile("(?P<inner_url>(?:http://)?(?:www\.)?modovideo\.com/frame\.php\?v=(?P<id>\w+))")]
        ),
        "control": "SM_SEEK", 
        "video_control": None
    }
    
    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "modovideo.com"
        self.url = url
        
    def suportaSeekBar(self): return True
    
    def getLink(self):
        vquality = int(self.params.get("qualidade", 2))
        optToNotFound = self.configs.get(1, None)
        optToNotFound = self.configs.get(2, optToNotFound)
        optToNotFound = self.configs.get(3, optToNotFound)
        return self.configs.get(vquality, optToNotFound)

    def start_extraction(self, proxies={}, timeout=25):
        video_id = Universal.get_video_id(self.basename, self.url)
        url = 'http://www.modovideo.com/video.php?v=%s'%video_id
        
        fd = self.connect(url, proxies=proxies, timeout=timeout)
        webpage = fd.read(); fd.close()

        try: self.configs["title"] = re.search("<title.*>(.+?)</title>", webpage).group(1)
        except:
            try: self.configs["title"] = re.search("<meta name=\"title\" content=\"(.+?)\"\s*/>", webpage).group(1)
            except: self.configs["title"] = get_radom_title() # usa um titulo gerado de caracteres aleatórios
            
        # o link está dentro de <iframe>
        ## playerUrl = re.search('(?:<iframe)?.+?src="(.+?frame\.php\?v=.+?)"', webpage).group(1)
        playerUrl = "http://www.modovideo.com/frame.php?v=%s"%video_id
        
        fd = self.connect(playerUrl, proxies=proxies, timeout=timeout)
        script = fd.read(); fd.close()

        matchobj = re.search("\.setup\(\{\s*flashplayer:\s*\"(.+)\"", script, re.DOTALL|re.IGNORECASE)
        qs_dict = cgi.parse_qs( matchobj.group(1) )
        videoUrl = qs_dict["player5plugin.video"][0]

        # guarda a url para atualizar nas configs
        self.configs[1] = videoUrl + "?start="
