import re

from ._sitebase import SiteBase
from main.app.util import sites


class JavaScriptPacked(object):
    def __init__(self, encoded, base, counter, params):
        self.encoded = encoded
        self.counter = counter
        self.base = base
        self.params = params

    @staticmethod
    def base36encode(number):
        if not isinstance(number, int):
            raise TypeError('number must be an integer')
        if number < 0:
            raise ValueError('number must be positive')
        alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        base36 = ''
        while number:
            number, i = divmod(number, 36)
            base36 = alphabet[i] + base36
        return base36 or alphabet[0]

    def unpacked(self):
        def _inner(encoded, base, counter, *args):
            assert base == 36, "base not is 36"
            for index in range(counter - 1, -1, -1):
                if args[index]:
                    code = self.base36encode(index).lower()
                    pattern = re.compile(u"\\b{0}\\b".format(code), re.DOTALL)
                    encoded = pattern.sub(args[index], encoded)
            return encoded
        return _inner(self.encoded, self.base, self.counter, *self.params.split("|"))


class VidigBiz(SiteBase):
    ##
    # http://vidig.biz/embed-82bbo33w237l-518x392.html
    ##
    controller = {
        "url": "http://vidig.biz/embed-%s-518x392.html",
        "patterns": [
            re.compile("(?P<inner_url>http://vidig\.biz/embed\-(?P<id>\w+)\-\d+x\d+.html)")
        ],
        "control": "SM_SEEK",
        "video_control": None
    }

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "vidig.biz"
        self.url = url

    def start_extraction(self, proxies={}, timeout=25):
        request = self.connect(self.url, proxies=proxies, timeout=timeout)
        page = request.text
        request.close()

        pattern = re.compile('file\s*:\s*(?:"|\')(.+?)(?:"|\')', re.DOTALL)

        try:
            match_obj = pattern.search(page)
            url = match_obj.group(1)
        except (AttributeError, re.error):
            match_obj = re.search('eval\((.+)\)', page, re.DOTALL)

            data = match_obj.group(1)
            data = data.replace('\\', '')
            data = data.replace('"', "'")

            match_obj = re.search(
                "p:'(?P<encoded>.+?)'\s*,\s*(?P<base>\d+)\s*,\s*(?P<counter>\d+)\s*,\s*'(?P<params>.+?)'\.split\('|'\)$",
                data)

            js = JavaScriptPacked(
                "p:" + str(match_obj.group('encoded')),
                int(match_obj.group('base')),
                int(match_obj.group('counter')),
                match_obj.group('params')
            )
            unpacked = js.unpacked()

            match_obj = pattern.search(unpacked)
            url = match_obj.group(1)
        try:
            match_obj = re.search('duration: "(\d+)"', page, re.DOTALL)
            duration = match_obj.group(1)
        except(AttributeError, re.error):
            duration = 0

        self.configs = {
            'title': sites.get_random_text(),
            'url': url + '&start=',
            'ext': 'mp4',
            'duration': duration
        }