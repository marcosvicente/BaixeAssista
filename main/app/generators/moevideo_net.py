# coding: utf-8
from ._sitebase import *

###################################### MOEVIDEO #######################################
class MoeVideo( SiteBase ):
    ## http://moevideo.net/video.php?file=64141.60e02b3b80c5e95e2e4ac85f0838&width=600&height=450
    ## http://moevideo.net/?page=video&uid=79316.7cd2a2d4b5e02fd77f017bbc1f01
    controller = {
        "url": "http://moevideo.net/video.php?file=%s", 
        "patterns":(
             re.compile("(?P<inner_url>http://moevideo\.net/\?page=video&uid=(?P<id>\w+\.\w+))"),
            [re.compile("(?P<inner_url>http://moevideo\.net/video\.php\?file=(?P<id>\w+\.\w+))")]
        ),
        "control": "SM_RANGE", 
        "video_control": None
    }

    def __init__(self, url, **params):
        """Constructor"""
        SiteBase.__init__(self, **params)
        self.apiUrl = "http://api.letitbit.net/"
        self.basename = "moevideo.net"
        self.url = url
        
    def suportaSeekBar(self):
        return True

    def getPostData(self, video_id):
        encoder = json.JSONEncoder()
        post = {"r": encoder.encode(
            ["tVL0gjqo5", 
             ["preview/flv_image",{"uid":"%s"%video_id}], 
             ["preview/flv_link",{"uid":"%s"%video_id}]])
                }
        return urllib.parse.urlencode( post )

    def extratcLink(self, videoinfo):
        link = ""
        if videoinfo["status"].lower() == "ok":
            for info in videoinfo["data"]:
                if type(info) is dict and "link" in info:
                    link = info["link"]
                    break
        return link

    def extraticTitle(self, url):
        title = url.rsplit("/", 1)[-1]
        title = title.rsplit(".", 1)[0]
        return title

    def setErrorMessage(self, url, videoinfo):
        if not url:
            if videoinfo["status"].lower() == "fail":
                msg = videoinfo["data"]
            else:
                if "not_found" in videoinfo["data"]:
                    msg = "file not found"
                else:
                    msg = videoinfo["data"][0]
            self.message = msg

    def start_extraction(self, proxies={}, timeout=25):
        video_id = Universal.get_video_id(self.basename, self.url)
        postdata = self.getPostData( video_id )
        
        fd = self.connect(self.apiUrl, proxies=proxies, timeout=timeout, data=postdata)
        webdata = fd.read(); fd.close()
        
        videoinfo = json.loads( webdata)
        url = self.extratcLink( videoinfo)
        
        try: self.setErrorMessage(url, videoinfo)
        except:pass

        # obtendo o t�tulo do video
        try: title = self.extraticTitle( url)
        except: title = sites.get_random_text()

        self.configs = {"url": url, "title": title}
        
        