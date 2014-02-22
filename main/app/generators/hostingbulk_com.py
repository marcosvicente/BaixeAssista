# coding: utf-8
from ._sitebase import *

#######################################################################################
class Hostingbulk( SiteBase ):
    """"""
    ## http://hostingbulk.com/jp33tfqh8835.html
    ## http://hostingbulk.com/embed-jp33tfqh8835-600x480.html
    ## http://hostingbulk.com/d74oyrowf9p6.html
    ## http://hostingbulk.com/xmpxw53emp7x.html
    controller = {
        "url": "http://hostingbulk.com/%s.html", 
        "patterns": (
             re.compile("(?P<inner_url>http://hostingbulk\.com/(?P<id>\w+)\.html)"),
            [re.compile("(?P<inner_url>http://hostingbulk\.com/embed\-?(?P<id>\w+)\-?(?:\d+x\d+)?\.html)")]
        ),
        "control": "SM_SEEK",
        "video_control": None
    }
    def suportaSeekBar(self):
        return True
    
    @staticmethod
    def base36encode( number ):
        if not isinstance(number, int):
            raise TypeError('number must be an integer')
        if number < 0:
            raise ValueError('number must be positive')
        alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        base36 = ''
        while number:
            number, i = divmod(number, 36)
            base36 = alphabet[i] + base36

        return base36 or alphabet[0]

    @staticmethod
    def unpack_params(p, a, c, k, e=None, d=None):
        for index in range(c-1, -1, -1):
            pattern = r"\b%s\b"%Hostingbulk.base36encode( index ).lower()
            p = re.sub(pattern, k[ index ], p, re.M|re.DOTALL)
        return p.replace(r"\'", "'")

    #----------------------------------------------------------------------
    def __init__(self, url, **params):
        """Constructor"""
        SiteBase.__init__(self, **params)
        self.basename = "hostingbulk.com"
        self.url = url

    def start_extraction(self, proxies={}, timeout=25):
        video_id = Universal.get_video_id(self.basename, self.url)
        url = self.controller["url"] % video_id

        fd = self.connect(url, proxies=proxies, timeout=timeout)
        webpage = fd.read(); fd.close()

        matchobj = re.search("eval\(\s*function\s*\(.*\)\s*{.*?}\s*(.+)\)", webpage)
        if matchobj:
            params = matchobj.group(1)
            
            matchobj = re.search("'(?P<ps>(.+?))'\s*,\s*(?P<n1>\d+?),\s*(?P<n2>\d+?),\s*'(?P<lps>.+?)\.split.+", params)
            uparams = self.unpack_params( matchobj.group("ps"), int(matchobj.group("n1")), int(matchobj.group("n2")), matchobj.group("lps").split("|"))
            
            url = re.search("'file'\s*,\s*'(.+?)'", uparams).group(1)
            pattern = "(http://.+?)//"; search = re.search(pattern, url)
            if search: url = re.sub(pattern, search.group(1)+"/d/", url)
        else:
            matchobj = re.search("setup\(\{.*?(?:'|\")file(?:'|\")\s*:\s*(?:'|\")(.+?)(?:'|\")", webpage, re.DOTALL)
            url = matchobj.group(1)
            try:
                matchobj = re.search("setup\(\{.*?(?:'|\")duration(?:'|\")\s*:\s*(?:'|\")(.+?)(?:'|\")", webpage, re.DOTALL)
                duration = int(matchobj.group(1))
            except:
                duration = None
        
        try: title = re.search("<title>(.+)</title>", webpage).group(1)
        except: title = sites.get_random_text()
        
        self.configs = {"url": url+"?start=", "title": title, "duration": duration}
        
        
        
        
        