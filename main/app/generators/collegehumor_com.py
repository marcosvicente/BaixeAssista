# coding: utf-8
import xml
import re

from ._sitebase import SiteBase
from main.app.generators import Universal


class CollegeHumor(SiteBase):
    """ Information extractor for collegehumor.com """
    # http://www.collegehumor.com/video/6768211/hardly-working-the-human-gif
    controller = {
        "url": "http://www.collegehumor.com/video/%s",
        "patterns": re.compile(
            r'(?P<inner_url>^(?:https?://)?(?:www\.)?collegehumor\.com/(?:video|embed)/(?P<id>[0-9]+)/.+)'),
        "control": "SM_RANGE",
        "video_control": None
    }

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "collegehumor.com"
        self.url = url

    def start_extraction(self, proxies={}, timeout=25):
        video_id = Universal.get_video_id(self.basename, self.url)
        request = self.connect(self.url, proxies=proxies, timeout=timeout)
        page = request.text
        request.close()

        matchobj = re.search(r'id="video:(?P<internalvideoid>[0-9]+)"', page)
        internal_video_id = matchobj.group('internalvideoid')

        info = {'id': video_id, 'internal_id': internal_video_id}
        xmlUrl = 'http://www.collegehumor.com/moogaloop/video:' + internal_video_id

        request = self.connect(xmlUrl, proxies=proxies, timeout=timeout)
        xml_data = request.text
        request.close()

        doc = xml.etree.ElementTree.fromstring(xml_data)
        video_node = doc.findall('./video')[0]

        info['title'] = video_node.findall('./caption')[0].text
        info['url'] = video_node.findall('./file')[0].text
        try:
            info['description'] = video_node.findall('./description')[0].text
            info['thumbnail'] = video_node.findall('./thumbnail')[0].text
            info['ext'] = info['url'].rpartition('.')[2]
            info['format'] = info['ext']
        except:
            pass
        self.configs = info