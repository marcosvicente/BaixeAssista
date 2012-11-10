# coding: utf-8
from _sitebase import *

###################################### PUTLOCKER ######################################
class PutLocker( SiteBase ):
    ## http://www.putlocker.com/file/3E3190548EE7A2BD
    controller = {
        "url": "http://www.putlocker.com/file/%s", 
        "patterns": (
            re.compile("(?P<inner_url>(?:http://)?www\.putlocker\.com/file/(?P<id>\w+))"),
            [re.compile("(?P<inner_url>(?:http://)?www\.putlocker\.com/embed/(?P<id>\w+))")]
            ),
        "control": "SM_RANGE",
        "video_control": None
    }
    patternForm = re.compile(
        '<form method="post">.*?<input.+?(?:value="(?P<hash>\w+)|name="(?P<name>\w+)")'
        '.*?(?:value="(?P<_hash>\w+)|name="(?P<_name>\w+)").*?<input.*value="(?P<confirm>[\w\s]+)"', 
        re.DOTALL|re.IGNORECASE
    )
    
    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.getFileBaseUrl = "http://www.putlocker.com"
        self.basename = "putlocker.com"
        self.url = url

    def suportaSeekBar(self):
        return True
    
    def getMessage(self, webpage):
        ## <div class='message t_0'>This file doesn't exist, or has been removed.</div>
        try:
            matchobj = re.search("<div class='message t_\d+'>(.*?)</div>", webpage)
            msg = "%s informa: %s"%(self.basename, unicode(matchobj.group(1),"utf-8"))
        except: msg = ""
        return msg

    @staticmethod
    def unescape(s):
        s = s.replace("&lt;", "<")
        s = s.replace("&gt;", ">")
        # this has to be last:
        s = s.replace("&amp;", "&")
        return s

    def start_extraction(self, proxies={}, timeout=25):
        # página web inicial
        url = self.url.replace("/embed","/file")
        fd = self.connect(url, proxies=proxies, timeout=timeout)
        webpage = fd.read(); fd.close()

        # messagem de erro. se houver alguma
        self.message = self.getMessage( webpage )

        # padrão captua de dados
        matchobj = self.patternForm.search( webpage )
        hashvalue =  matchobj.group("hash") or  matchobj.group("_hash")
        hashname = matchobj.group("name") or  matchobj.group("_name")
        confirmvalue = matchobj.group("confirm")

        data = urllib.urlencode({hashname: hashvalue, "confirm": confirmvalue})
        fd = self.connect(url, proxies=proxies, timeout=timeout, data=data)
        webpage = fd.read(); fd.close()

        # extraindo o titulo.
        try: title = re.search("<title>(.*?)</title>", webpage).group(1)
        except: title = sites.get_random_text()

        # começa a extração do link vídeo.
        ## playlist: '/get_file.php?stream=WyJORVE0TkRjek5FUkdPRFJETkRKR05Eb3',
        pattern = "playlist:\s*(?:'|\")(/get_file\.php\?stream=.+?)(?:'|\")"
        matchobj = re.search(pattern, webpage, re.DOTALL|re.IGNORECASE)
        url = self.getFileBaseUrl + matchobj.group(1)
        
        # começa a análize do xml
        fd = self.connect(url, proxies=proxies, timeout=timeout)
        rssData = fd.read(); fd.close()

        ext = "flv" # extensão padrão.
        ## print rssData
        
        # url do video.
        url = re.search("<media:content url=\"(.+?)\"", rssData).group(1)
        url = self.unescape( url ).replace("'","").replace('"',"")
        
        try: ext = re.search("type=\"video/([\w-]+)", rssData).group(1)
        except: pass # usa a extensão padrão.
        
        self.configs = {"url": url+"&start=", "title":title, "ext": ext}