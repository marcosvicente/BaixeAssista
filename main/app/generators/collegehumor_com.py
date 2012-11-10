from _sitebase import *

##################################### COLLEGEHUMOR ####################################
class CollegeHumor( SiteBase ):
    """Information extractor for collegehumor.com"""
    ## http://www.collegehumor.com/video/6768211/hardly-working-the-human-gif
    controller = {
        "url": "http://www.collegehumor.com/video/%s", 
        "patterns": re.compile(r'(?P<inner_url>^(?:https?://)?(?:www\.)?collegehumor\.com/(?:video|embed)/(?P<id>[0-9]+)/.+)'), 
        "control": "SM_RANGE", 
        "video_control": None
    }
    
    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "collegehumor.com"
        self.url = url

    def start_extraction(self, proxies={}, timeout=25):
        video_id = Universal.get_video_id(self.basename, self.url)
        try:
            fd = self.connect(self.url, proxies=proxies, timeout=timeout)
            webpage = fd.read(); fd.close()
        except: return # falha obtendo a página

        m = re.search(r'id="video:(?P<internalvideoid>[0-9]+)"', webpage)
        if m is None: return

        internal_video_id = m.group('internalvideoid')

        info = {'id': video_id, 'internal_id': internal_video_id}
        xmlUrl = 'http://www.collegehumor.com/moogaloop/video:' + internal_video_id
        try:
            fd = self.connect(xmlUrl, proxies=proxies, timeout=timeout)
            metaXml = fd.read(); fd.close()
        except: return # falha obtendo dados xml

        mdoc = xml.etree.ElementTree.fromstring(metaXml)
        videoNode = mdoc.findall('./video')[0]
        info['title'] = videoNode.findall('./caption')[0].text
        info['url'] = videoNode.findall('./file')[0].text
        try:    
            info['description'] = videoNode.findall('./description')[0].text
            info['thumbnail'] = videoNode.findall('./thumbnail')[0].text
            info['ext'] = info['url'].rpartition('.')[2]
            info['format'] = info['ext']
        except: pass

        self.configs = info