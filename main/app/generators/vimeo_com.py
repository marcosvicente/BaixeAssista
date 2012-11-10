from _sitebase import *

######################################## VIMEO ########################################
class Vimeo( SiteBase ):
    """Information extractor for vimeo.com."""
    ## http://vimeo.com/40620829
    ## http://vimeo.com/channels/news/40620829
    ## http://vimeo.com/channels/hd/40716035
    controller = {
        "url": "http://vimeo.com/%s", 
        "patterns": re.compile(r'(?P<inner_url>(?:https?://)?(?:(?:www|player).)?vimeo\.com/(?:groups/[^/]+/|channels?/(?:news/|hd/))?(?:videos?/)?(?P<id>[0-9]+))'), 
        "control": "SM_RANGE", 
        "video_control": None
    }
    
    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = u"vimeo.com"
        self.url = url

    def start_extraction(self, proxies={}, timeout=25):
        try:
            # extrai o id do video
            video_id = Universal.get_video_id(self.basename, self.url)
            url = "http://vimeo.com/moogaloop/load/clip:%s" % video_id

            fd = self.connect(url, proxies=proxies, timeout=timeout)
            webpage = fd.read(); fd.close()
        except: return # falha obtendo a página

        try:# Extract title
            mobj = re.search(r'<caption>(.*?)</caption>', webpage)
            video_title = mobj.group(1).decode('utf-8')
        except:
            video_title = get_radom_title()

        try:# Extract uploader
            mobj = re.search(r'<uploader_url>http://vimeo.com/(.*?)</uploader_url>', webpage)
            video_uploader = mobj.group(1).decode('utf-8')
        except:
            video_uploader = ""

        try:# Extract video thumbnail
            mobj = re.search(r'<thumbnail>(.*?)</thumbnail>', webpage)
            video_thumbnail = mobj.group(1).decode('utf-8')
        except:
            video_thumbnail = ""

        video_description = 'Foo.'

        # Vimeo specific: extract request signature
        mobj = re.search(r'<request_signature>(.*?)</request_signature>', webpage)
        sig = mobj.group(1).decode('utf-8')

        # Vimeo specific: extract video quality information
        mobj = re.search(r'<isHD>(\d+)</isHD>', webpage)
        quality = mobj.group(1).decode('utf-8')

        if int(quality) == 1: quality = 'hd'
        else: quality = 'sd'

        # Vimeo specific: Extract request signature expiration
        mobj = re.search(r'<request_signature_expires>(.*?)</request_signature_expires>', webpage)
        sig_exp = mobj.group(1).decode('utf-8')

        ## http://player.vimeo.com/play_redirect?clip_id=36031564&sig=10e1f89cb26ab0221c84fbc35b2051ec&time=1335225117&quality=hd&codecs=H264,VP8,VP6&type=moogaloop_local&embed_location=
        ## video_url = "http://vimeo.com/moogaloop/play/clip:%s/%s/%s/?q=%s" % (video_id, sig, sig_exp, quality)
        video_url = "http://player.vimeo.com/play_redirect?clip_id=%s&sig=%s&time=%s&quality=%s" % (video_id, sig, sig_exp, quality)

        self.configs = {
            'id':        video_id.decode('utf-8'),
            'url':        video_url,
            'uploader':    video_uploader,
            'upload_date':    u'NA',
            'title':    video_title,
            'ext':        u'mp4',
            'thumbnail':    video_thumbnail.decode('utf-8'),
            'description':    video_description,
            'thumbnail':    video_thumbnail,
            'description':    video_description,
            'player_url':    None,
        }