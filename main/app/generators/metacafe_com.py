from _sitebase import *

###################################### METACAFE #######################################
class Metacafe( SiteBase ):
    """Information Extractor for metacafe.com."""
    ## http://www.metacafe.com/watch/8492972/wheel_of_fortune_fail/
    controller = {
        "url": "http://www.metacafe.com/watch/%s/", 
        "patterns": re.compile("(?P<inner_url>(?:http://)?www\.metacafe\.com/watch/(?P<id>\w+)/.*)"), 
        "control": "SM_RANGE", 
        "video_control": None
    }

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "metacafe.com"
        self.url = url
        
    def getLink(self):
        vquality = int(self.params.get("qualidade", 2))
        optToNotFound = self.configs.get(1, None)
        optToNotFound = self.configs.get(2, optToNotFound)
        optToNotFound = self.configs.get(3, optToNotFound)
        return self.configs.get(vquality, optToNotFound)
    
    def start_extraction(self, proxies={}, timeout=25):
        video_id = Universal.get_video_id(self.basename, self.url)
        
        url = "http://www.metacafe.com/watch/%s/" % video_id
        fd = self.connect( url, proxies=proxies, timeout=timeout)
        webpage = fd.read(); fd.close()
        
        matchobj = re.search("flashVarsCache\s*=\s*\{(.*?)\}", webpage)
        flashvars = urllib.unquote_plus(matchobj.group(1))
        
        matchobj = re.search("\"mediaData\".+?\"mediaURL\"\s*:\s*\"(.*?)\".*\"key\"\s*:\s*\"(.*?)\".*\"value\"\s*:\s*\"(.*?)\"", flashvars)
        lowMediaURL = urllib.unquote_plus(matchobj.group(1)) +"?%s=%s" % (matchobj.group(2), matchobj.group(3))
        lowMediaURL = lowMediaURL.replace("\/", "/")
        
        matchobj = re.search("\"highDefinitionMP4\".+?\"mediaURL\"\s*:\s*\"(.*?)\".*\"key\"\s*:\s*\"(.*?)\".*\"value\"\s*:\s*\"(.*?)\"", flashvars)
        highMediaURL = urllib.unquote_plus(matchobj.group(1)) +"?%s=%s" % (matchobj.group(2), matchobj.group(3))
        highMediaURL = highMediaURL.replace("\/", "/")
        
        try: title = re.search("<title>(.+)</title>", webpage).group(1)
        except: title = get_radom_title()
        
        self.configs = {1: lowMediaURL, 2: highMediaURL, 'title': title}