from _sitebase import *

###################################### ANIMETUBE #######################################
class Anitube( SiteBase ):
    ## http://www.anitube.jp/video/43595/Saint-Seiya-Omega-07
    controller = {
        "url": "http://www.anitube.jp/video/%s", 
        "patterns": re.compile("(?P<inner_url>http://www\.anitube\.jp/video/(?P<id>\w+))"),
        "control": "SM_RANGE", 
        "video_control": None
    }
    
    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "anitube.jp"
        self.url = url

    def suportaSeekBar(self):
        return True

    def start_extraction(self, proxies={}, timeout=25):
        fd = self.connect(self.url, proxies=proxies, timeout=timeout)
        webdata = fd.read(); fd.close()
        
        ## addParam("flashvars",'config=http://www.anitube.jp/nuevo/config.php?key=c3ce49fd327977f837ab')
        ##<script type="text/javascript">var cnf=
        try:
            mathobj = re.search("addParam\(\"flashvars\",\s*'config=\s*(?P<url>.+?)'\)", webdata, re.DOTALL)            
            url = mathobj.group("url")
        except:
            mathobj = re.search("\<script type=\"text/javascript\"\>\s*var\s*cnf\s*=\s*(?:'|\")(?P<url>.+?)(?:'|\")", webdata, re.DOTALL)            
            url = mathobj.group("url")

        ## <file>http://lb01-wdc.anitube.com.br/42f56c9f566c1859da833f80131fdcd5/4fafe9c0/43595.flv</file>
        ## <title>Saint Seiya Omega 07</title>
        fd = self.connect(url, proxies=proxies, timeout=timeout)
        xmldata = fd.read(); fd.close()

        if not re.match("http://www.anitube\.jp/nuevo/playlist\.php", url):
            play_url = re.search("<playlist>(.*?)</playlist>", xmldata).group(1)
            fd = self.connect(play_url, proxies=proxies, timeout=timeout)
            xmldata = fd.read(); fd.close()

        video_url = re.search("<file>(.*?)</file>", xmldata).group(1)

        try: title = re.search("<title>(.*?)</title>", xmldata).group(1)
        except: title = get_radom_title()

        self.configs = {"url": video_url+"?start=", "title": title}