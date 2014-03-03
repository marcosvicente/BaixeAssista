import re

from ._sitebase import SiteBase
from main.app.generators import Universal
from main.app.util import sites


__author__ = 'alex'


class DropVideo(SiteBase):
    ##
    # http://megafilmeshd.net/player/drop.php?v=FeOYgLEMNd
    # http://dropvideo.com/embed/FeOYgLEMNd/
    ##
    controller = {
        "url": "http://dropvideo.com/embed/%s",
        "patterns": (
            re.compile("(?P<inner_url>http://megafilmeshd\.net/player/drop\.php?v=(?P<id>\w+))"),
            [re.compile("(?P<inner_url>http://dropvideo\.com/embed/(?P<id>\w+))")],
        ),
        "control": "SM_RANGE",
        "video_control": None
    }

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "dropvideo.com"
        self.embed_url = 'http://dropvideo.com/embed/%s'
        self.url = url

    def start_extraction(self, *args, **kwargs):
        video_id = Universal.get_video_id(self.basename, self.url)
        request = self.connect(self.embed_url % video_id, *args, **kwargs)
        page = request.text
        request.close()
        ##
        # var vurl = "http://fs004.dropvideo.com/v/5a2e3a944f6e498488c93b0aac9719a7.mp4?st=h6RJOM57p-4JgLLB2C2lRA"
        ##
        match_obj = re.search('vurl\s*=\s*\"(.+?)\"', page, re.DOTALL)
        url = match_obj.group(1)

        try:
            match_obj = re.search('vtitle\s*=\s*"(.+?)"', page, re.DOTALL)
            title = match_obj.group(1)
        except:
            title = sites.get_random_text()

        self.configs = {'url': url, 'title': title}