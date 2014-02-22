# Create your views here.
import urllib.request, urllib.parse, urllib.error

from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import render_to_response


def stream_loader(request):
    if not request.manage:
        return HttpResponse("waiting...")

    manage = request.manage
    video_manager = manage.videoManager
    seek_pos = request.GET.get("start", 0)

    try:
        seek_pos = int(seek_pos)
    except ValueError:
        seek_pos = video_manager.get_relative_mp4(seek_pos)

    if seek_pos > 0 and manage.videoManager.suportaSeekBar():
        manage.setRandomRead(seek_pos)
        status_code = 206
    else:
        manage.reloadSettings()
        status_code = 200

    filename = manage.getVideoTitle()
    filename = filename.encode("utf-8", "ignore")
    video_size = manage.getVideoSize()
    video_type = manage.getVideoExt()

    response = StreamingHttpResponse(manage.get_streamer(), status=status_code)
    response["Content-Type"] = "video/%s" % video_type
    response["Content-Length"] = video_size
    response["Content-Transfer-Encoding"] = "binary"
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    response["Accept-Ranges"] = "bytes"
    return response


def player_loader(request):
    params = request.GET.copy()
    for key in params: params[key] = urllib.parse.unquote_plus(params[key])
    return render_to_response(params["template"], {"params": params},
                              mimetype="text/html")