# coding: utf-8
from _sitebase import *

###################################### REDTUBE #######################################
class Pornhub( SiteBase ):
    ## http://www.pornhub.com/view_video.php?viewkey=1156461684&utm_source=embed&utm_medium=embed&utm_campaign=embed-logo
    controller = {
        "url": "http://www.pornhub.com/view_video.php?viewkey=%s", 
        "patterns": (
             re.compile("(?P<inner_url>http://www\.pornhub\.com/view_video\.php\?viewkey=(?P<id>\w+))"),
            [re.compile("(?P<inner_url>http://www\.pornhub\.com/view_video\.php\?viewkey=(?P<id>\w+).*&utm_source=embed)")]
            ),
        "control": "SM_SEEK",
        "video_control": None
    }

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.apiUrl = "http://www.pornhub.com/embed_player.php?id=%s"
        self.basename = "pornhub.com"
        self.url = url
        
    def suportaSeekBar(self):
        return True

    def start_extraction(self, proxies={}, timeout=25):
        fd = self.connect(self.url, proxies=proxies, timeout=timeout)
        webpage = fd.read(); fd.close()
        try:
            fs = ""
            matchobj = re.search('''(?:"|')video_url(?:"|')\s*:\s*(?:"|')(.+?)(?:"|')''', webpage, re.DOTALL)
            try: url = base64.b64decode(urllib.unquote_plus(matchobj.group(1)))
            except: url = urllib.unquote_plus(matchobj.group(1))
            
            matchobj = re.search('''(?:"|')video_title(?:"|')\s*:\s*(?:"|')(.*?)(?:"|')''', webpage, re.DOTALL)
            try: title = urllib.unquote_plus( matchobj.group(1) )
            except: title = get_radom_title()
        except:
            urlid = Universal.get_video_id(self.basename, self.url)
            fd = self.connect(self.apiUrl % urlid, proxies=proxies, timeout=timeout)
            xmlData = fd.read(); fd.close()
            
            url = re.search("""<video_url><!\[CDATA\[(.+)\]\]></video_url>""", xmlData).group(1)

            try: title = re.search("<video_title>(.*)</video_title>", xmlData).group(1)
            except: title = get_radom_title()
            
            try: fs = re.search("<flvStartAt>(.+)</flvStartAt>", xmlData).group(1)
            except: fs = ""
            
        self.configs = {"url": url+(fs or "&fs="), "title": (title or get_radom_title())}