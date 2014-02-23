import re

from ._sitebase import SiteBase
from main.app.util import sites


class Vk(SiteBase):
    ## http://vk.com/video_ext.php?oid=164478778&id=163752296&hash=246b8447ed557240&hd=1
    ## http://vk.com/video103395638_162309869?hash=23aa2195ccec043b
    controller = {
        "url": "http://vk.com/video_ext.php?%s",
        "patterns": (
            re.compile("(?P<inner_url>http://vk\.com/(?P<id>video\d+_\d+\?hash=\w+))"),
            [re.compile("(?P<inner_url>http://vk\.com/video_ext\.php\?(?P<id>oid=\w+&id=\w+&hash=\w+(?:&hd=\d+)?))")]
        ),
        "control": "SM_RANGE",
        "video_control": None
    }

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "vk.com"
        self.url = url

    def random_mode(self):
        return True

    def get_link(self):
        video_quality = int(self.params.get("quality", 2))
        when_not_fount = self.configs.get(1, None)
        when_not_fount = self.configs.get(2, when_not_fount)
        when_not_fount = self.configs.get(3, when_not_fount)
        return self.configs.get(video_quality, when_not_fount)

    def message_discover(self, web_page):
        _message = "This video has been removed from public access."
        pattern = re.compile(_message, re.I | re.DOTALL)
        if pattern.search(web_page):
            self.message = _message
        else:
            self.message = ''

    def start_extraction(self, proxies={}, timeout=25):
        ## http://cs519609.userapi.com/u165193745/video/7cad4a848e.360.mp4
        fd = self.connect(self.url, proxies=proxies, timeout=timeout)
        web_data = str(fd.read())
        fd.close()
        self.message_discover(web_data)
        params = {}
        try:
            math_obj = re.search("var\s*video_host\s*=\s*'(?P<url>.+?)'", web_data, re.DOTALL)
            params["url"] = math_obj.group("url")

            math_obj = re.search("var\s*video_uid\s*=\s*'(?P<uid>.+?)'", web_data, re.DOTALL)
            params["uid"] = math_obj.group("uid")

            math_obj = re.search("var\s*video_vtag\s*=\s*'(?P<vtag>.+?)'", web_data, re.DOTALL)
            params["vtag"] = math_obj.group("vtag")

            math_obj = re.search("var\s*video_max_hd\s*=\s*(?:')?(?P<max_hd>.+?)(?:')?", web_data, re.DOTALL)
            params["max_hd"] = math_obj.group("max_hd")

            math_obj = re.search("var\s*video_no_flv\s*=\s*(?:')?(?P<no_flv>.+?)(?:')?", web_data, re.DOTALL)
            params["no_flv"] = math_obj.group("no_flv")
        except:
            match_obj = re.search("var\s*vars\s*=\s*\{(?P<vars>.+?)\}", web_data, re.DOTALL)
            raw_params = match_obj.group("vars").replace(r'\"', '"')
            params = dict([(a, (b or c)) for a, b, c in re.findall('"(.+?)"\s*:\s*(?:"(.*?)"|(-?\d*))', raw_params)])
            params["url"] = "http://cs%s.vk.com" % params.pop("host")

        try:
            match_obj = re.search("<title>(.+?)</title>", web_data)
            title = match_obj.group(1)
        except:
            title = sites.get_random_text()

        if int(params.get("no_flv", 0)):
            base_url = params["url"] + "/u%s/videos/%s.{res}.mp4" % (params["uid"], params["vtag"])
            if params.get('url240', '').startswith('http'):
                url_hd240 = params['url240'].replace("\\", '')
            else:
                url_hd240 = base_url.format(res=240)
            if params.get('url360', '').startswith('http'):
                url_hd360 = params['url360'].replace("\\", '')
            else:
                url_hd360 = base_url.format(res=360)
            ext = "mp4"
        else:
            url_hd240 = url_hd360 = params["url"] + "u%s/videos/%s.flv" % (params["uid"], params["vtag"])
            ext = "flv"

        self.configs = {"title": title, "ext": ext, 1: url_hd240, 2: url_hd360}