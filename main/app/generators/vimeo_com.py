import re

from main.app.generators import Universal
from ._sitebase import SiteBase
from main.app.util import sites


class Vimeo(SiteBase):
    """ Information extractor for vimeo.com """
    ##
    # http://vimeo.com/40620829
    # http://vimeo.com/channels/news/40620829
    # http://vimeo.com/channels/hd/40716035
    ##
    controller = {
        "url": "http://vimeo.com/%s",
        "patterns": re.compile(
            r'(?P<inner_url>(?:https?://)?(?:(?:www|player).)?vimeo\.com/(?:groups/[^/]+/|channels?/(?:news/|hd/))?(?:videos?/)?(?P<id>[0-9]+))'),
        "control": "SM_RANGE",
        "video_control": None
    }

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "vimeo.com"
        self.url = url

    def start_extraction(self, proxies={}, timeout=25):
        video_id = Universal.get_video_id(self.basename, self.url)
        url = "http://vimeo.com/moogaloop/load/clip:%s" % video_id
        request = self.connect(url, proxies=proxies, timeout=timeout)
        page = request.text
        request.close()

        try:
            video_title = re.search(r'<caption>(.*?)</caption>', page).group(1)
        except:
            video_title = sites.get_random_text()

        try:  # Extract uploader
            match_obj = re.search(r'<uploader_url>http://vimeo.com/(.*?)</uploader_url>', page)
            video_uploader = str(match_obj.group(1))
        except:
            video_uploader = ""

        try:  # Extract video thumbnail
            match_obj = re.search(r'<thumbnail>(.*?)</thumbnail>', page)
            video_thumbnail = str(match_obj.group(1))
        except:
            video_thumbnail = ''

        video_description = 'Foo.'

        # Vimeo specific: extract request signature
        match_obj = re.search(r'<request_signature>(.*?)</request_signature>', page)
        sig = str(match_obj.group(1))

        # Vimeo specific: extract video quality information
        match_obj = re.search(r'<isHD>(\d+)</isHD>', page)
        quality = str(match_obj.group(1))

        if int(quality) == 1:
            quality = 'hd'
        else:
            quality = 'sd'

        # Vimeo specific: Extract request signature expiration
        match_obj = re.search(r'<request_signature_expires>(.*?)</request_signature_expires>', page)
        sig_exp = str(match_obj.group(1))

        ##
        # http://player.vimeo.com/play_redirect?clip_id=36031564&sig=10e1f89cb26ab0221c84fbc35b2051ec&time=1335225117&
        # quality=hd&codecs=H264,VP8,VP6&type=moogaloop_local&embed_location=
        # video_url = "http://vimeo.com/moogaloop/play/clip:%s/%s/%s/?q=%s" % (video_id, sig, sig_exp, quality)
        ##
        video_url = "http://player.vimeo.com/play_redirect?clip_id=%s&sig=%s&time=%s&quality=%s"

        self.configs = {
            'id': str(video_id),
            'url': video_url % (video_id, sig, sig_exp, quality),
            'uploader': video_uploader,
            'upload_date': 'NA',
            'title': video_title,
            'ext': 'mp4',
            'thumbnail': video_thumbnail,
            'description': video_description,
            'player_url': None,
        }