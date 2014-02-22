# coding: utf-8

"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from main import environ

environ.setup(__name__ == "__main__")

from main.app.generators._sitebase import ConnectionBase
from main.app.manager.urls import UrlManager
from main.app.generators import Universal
from main.app.util import sites

#######################################################################################
def debug(video_control, **params):
    "MP4 File: %s" % video_control.is_mp4()

    if video_control.is_mp4():
        print(("MP4 Duration: {!s}".format(video_control.get_duration())))
        streamsize = params["streamsize"]
        videolink = params["videolink"]

        headersize = video_control.get_header_size()
        seekpos = 0

        seekpos = float("%.2f" % video_control.get_relative(seekpos))
        linkseek = sites.get_with_seek(videolink, seekpos)
        print(linkseek)

        fd = video_control.connect(linkseek)
        print(("Response: {!s}".format(
            ConnectionBase.check_response(headersize, seekpos, streamsize, fd.headers))
        ))

        print((repr(fd.read(512))))
        print((fd.headers.get("Content-Length", 0)))

        fd.close()


def checkSite(url, proxies={}, timeout=30, **params):
    """ verifica se o site dado por 'baseName' est� respondendo as requisi��es """
    basename = UrlManager.getBaseName(url)
    print(("Checking: ", basename))

    video_control = Universal.get_video_control(basename)
    video_control = video_control(url, **params)

    if video_control.get_video_info(1, proxies=proxies, timeout=timeout):
        videolink = video_control.get_link()
        streamsize = video_control.get_video_size()
        streamtitle = video_control.get_title()

        print(("Url: ", videolink))
        print(("Size: ", streamsize))
        print(("Title: ", streamtitle))
        print(("-" * 25))

        if params["debug"]:  # faz análizes sobre os dados retornados.
            debug(video_control, videolink=videolink, streamsize=streamsize,
                  streamtitle=streamtitle)
        return True
    else:
        print(("MSG: ", video_control.get_message()))
    print(("-" * 50))
    return False

#pxm = manager.ProxyManager()
#for n in range(pxm.get_num()):
#    proxies = pxm.get_formated()
#    print proxies["http"]
#    proxies = {}
#pxm.set_bad( proxies )
#del pxm

checkSite("http://www.youtube.com/watch?v=1iTg20x7w2s", proxies={}, quality=3, debug=True)
    
    
    
    
    
    
    