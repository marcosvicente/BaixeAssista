from _sitebase import *

##################################### PHOTOBUCKET #####################################
class Photobucket( SiteBase ):
    """Information extractor for photobucket.com."""
    ## http://photobucket.com/videos
    controller = {
        "url": "http://media.photobucket.com/video/%s", 
        "patterns": re.compile("(?P<inner_url>(?:http://)?media\.photobucket\.com/video/(?P<id>.*))"), 
        "control": "SM_RANGE", 
        "video_control": None
    }
    
    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "media.photobucket"
        self.url = url

    def start_extraction(self, proxies={}, timeout=25):
        video_extension = 'flv'

        # Retrieve video webpage to extract further information
        try:
            fd = self.connect(self.url, proxies=proxies, timeout=timeout)
            webpage = fd.read(); fd.close()
        except: return # falha obtendo a p�gina

        # Extract URL, uploader, and title from webpage
        mobj = re.search(r'<link rel="video_src" href=".*\?file=([^"]+)" />', webpage)
        mediaURL = urllib.unquote(mobj.group(1))
        video_url = mediaURL

        try:
            mobj = re.search(r'<meta name="description" content="(.+)"', webpage)
            video_title = mobj.group(1).decode('utf-8')
        except:
            video_title = get_radom_title()

        self.configs = {
            'url': video_url.decode('utf-8'),
            'upload_date': u'NA',
            'title': video_title,
            'ext': video_extension.decode('utf-8'),
            'format': u'NA',
            'player_url': None
        }