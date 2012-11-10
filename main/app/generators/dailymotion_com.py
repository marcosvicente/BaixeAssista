# coding: utf-8
from _sitebase import *

##################################### DAILYMOTION #####################################
class Dailymotion( SiteBase ):
    """Information Extractor for Dailymotion"""
    ## http://www.dailymotion.com/video/xowm01_justin-bieber-gomez-at-chuck-e-cheese_news#
    controller = {
        "url": "http://www.dailymotion.com/video/%s", 
        "patterns": re.compile(r"(?P<inner_url>(?i)(?:https?://)?(?:www\.)?dailymotion(?:\.com)?(?:[a-z]{2,3})?/video/(?P<id>.+))"), 
        "control": "SM_RANGE", 
        "video_control": None
    }
    
    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "dailymotion.com"
        self.url = url

    def start_extraction(self, proxies={}, timeout=25):
        video_id = Universal.get_video_id(self.basename, self.url)
        fd = self.connect(self.url, proxies=proxies, timeout=timeout, headers={'Cookie': 'family_filter=off'})
        webpage = fd.read(); fd.close()
        
        video_extension = 'flv'
        
        # Extract URL, uploader and title from webpage
        mobj = re.search(r'addVariable\(\"sequence\"\s*,\s*\"(.+?)\"\)', webpage, re.DOTALL|re.IGNORECASE)

        sequence = urllib.unquote(mobj.group(1))
        mobj = re.search(r',\"sdURL\"\:\"([^\"]+?)\",', sequence)
        mediaURL = urllib.unquote(mobj.group(1)).replace('\\', '')
        # if needed add http://www.dailymotion.com/ if relative URL
        video_url = mediaURL

        try:
            htmlParser = HTMLParser.HTMLParser()
            mobj = re.search(r'<meta property="og:title" content="(?P<title>[^"]*)" />', webpage)
            video_title = htmlParser.unescape(mobj.group('title'))
        except:
            video_title = get_radom_title()

        matchobj = re.search(r'(?im)<span class="owner[^\"]+?">[^<]+?<a [^>]+?>([^<]+?)</a></span>', webpage)
        video_uploader = matchobj.group(1)
        
        self.configs = {
            'id':        video_id.decode('utf-8'),
            'url':        video_url.decode('utf-8'),
            'uploader':    video_uploader.decode('utf-8'),
            'upload_date': u'NA',
            'title':    video_title,
            'ext':        video_extension.decode('utf-8'),
            'format':    u'NA',
            'player_url': None,
        }