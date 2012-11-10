from _sitebase import *

##################################### VIDEO.GOOGLE ####################################
class GoogleVideo( SiteBase ):
    """Information extractor for video.google.com."""
    ## http://video.google.com.br/videoplay?docid=-1717800235769991478
    controller = {
        "url": "http://video.google.com.br/videoplay?docid=%s", 
        "patterns": re.compile(r'(?P<inner_url>(?:http://)?video\.google\.(?:com(?:\.au)?(?:\.br)?|co\.(?:uk|jp|kr|cr)|ca|de|es|fr||it|nl|pl)/videoplay\?docid=(?P<id>-?[^\&]+).*)'), 
        "control": "SM_RANGE", 
        "video_control": None
    }
    
    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "video.google"
        self.url = url

    def start_extraction(self, proxies={}, timeout=25):
        video_id = Universal.get_video_id(self.basename, self.url)
        
        url = "http://video.google.com/videoplay?docid=%s&hl=en&oe=utf-8" % video_id
        fd = self.connect(url, proxies=proxies, timeout=timeout)
        webpage = fd.read(); fd.close()
        
        video_extension = "mp4"
        
        # Extract URL, uploader, and title from webpage
        mobj = re.search(r"download_url:'([^']+)'", webpage)
        if mobj is None:
            video_extension = 'flv'
            mobj = re.search(r"(?i)videoUrl\\x3d(.+?)\\x26", webpage)
        if mobj is None: return

        mediaURL = urllib.unquote(mobj.group(1))
        mediaURL = mediaURL.replace('\\x3d', '\x3d')
        mediaURL = mediaURL.replace('\\x26', '\x26')

        video_url = mediaURL

        mobj = re.search(r'<title>(.*)</title>', webpage)
        if mobj is None: return

        video_title = mobj.group(1).decode('utf-8')

        # Extract video description
        mobj = re.search(r'<span id=short-desc-content>([^<]*)</span>', webpage)
        if mobj is None: return

        video_description = mobj.group(1).decode('utf-8')
        if not video_description:
            video_description = 'No description available.'

        self.configs = {
            'id':        video_id.decode('utf-8'),
            'url':        video_url.decode('utf-8'),
            'uploader':    u'NA',
            'upload_date':    u'NA',
            'title':    video_title,
            'ext':        video_extension.decode('utf-8'),
            'format':    u'NA',
            'player_url': None,
        }