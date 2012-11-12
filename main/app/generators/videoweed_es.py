# coding: utf-8
from _sitebase import *

###################################### VIDEOWEED ######################################
class Videoweed( SiteBase ):
    ## http://www.videoweed.es/file/sackddsywnmyt
    ## http://embed.videoweed.es/embed.php?v=sackddsywnmyt
    controller = {
        "url": "http://www.videoweed.es/file/%s",
        "basenames": ["embed.videoweed", "videoweed.es"],
        "patterns": (
             re.compile("(?P<inner_url>(?:http://)?www\.videoweed\.es/file/(?P<id>\w+))"),
            [re.compile("(?P<inner_url>(?:http://)?embed\.videoweed\.es/embed\.php\?v=(?P<id>\w+))")]
        ),
        "control": "SM_SEEK", 
        "video_control": None
    }
    
    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.player_api = "http://www.videoweed.es/api/player.api.php?key=%s&user=undefined&codes=undefined&pass=undefined&file=%s"
        # link direto para o site(n�o embutido)
        self.siteVideoLink = "http://www.videoweed.es/file/%s"
        # parte principal da url usada como elemento chave no programa
        self.basename = manager.UrlManager.getBaseName( url )
        self.url = url
        
    def suportaSeekBar(self): return True
    
    def get_site_message(self, webpage):
        try:
            matchobj = re.search("<center>(?P<message>.+?)(?:</div>|</center>)", webpage, re.DOTALL)
            message = matchobj.group("message")
            message = message.decode("utf-8","ignore")
            message = re.sub("^[\s\t\n]+|[\n\s\t]+$", "", message)
        except: message = ""
        return message
        
    def getLink(self):
        vquality = int(self.params.get("qualidade", 2))
        optToNotFound = self.configs.get(1, None)
        optToNotFound = self.configs.get(2, optToNotFound)
        optToNotFound = self.configs.get(3, optToNotFound)
        return self.configs.get(vquality, optToNotFound)
        
    def start_extraction(self, proxies={}, timeout=25):
        url_id = Universal.get_video_id(self.basename, self.url)
        url = self.siteVideoLink % url_id

        fd = self.connect(url, proxies=proxies, timeout=timeout)
        webpage = fd.read(); fd.close()
        
        # message gerada caso o video tenha sido removido
        self.message = self.get_site_message(webpage)
        
        ## flashvars.filekey="189.24.243.113-505db61fc331db7a2a7fa91afb22e74d-"
        matchobj = re.search('flashvars\.filekey="(.+?)"', webpage)
        filekey = matchobj.group(1)
        
        url = self.player_api % (filekey, url_id) # ip; id
        fd = self.connect(url, proxies=proxies, timeout=timeout)
        info_data = fd.read(); fd.close()

        params = dict(re.findall("(\w+)=(.*?)&", info_data))

        url = urllib.unquote_plus( params["url"] )
        seekparm = urllib.unquote_plus( params["seekparm"] )

        if not seekparm: seekparm = "?start="
        elif seekparm.rfind("=") < 0: seekparm += "="
        
        try: title = urllib.unquote_plus( params["title"] )
        except: title = sites.get_random_text()
        
        self.configs = {1: url + seekparm, "title": title}