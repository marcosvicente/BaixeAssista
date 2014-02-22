# Create your views here.
import urllib.request
import urllib.parse
import urllib.error

from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import render_to_response


def stream_loader(request):
    if not request.manage:
        return HttpResponse("waiting...")

    manage = request.manage
    video_manager = manage.video_manager
    seek_pos = request.GET.get("start", 0)

    try:
        seek_pos = int(seek_pos)
    except ValueError:
        seek_pos = video_manager.get_relative_mp4(seek_pos)

    if seek_pos > 0 and manage.video_manager.random_mode():
        manage.set_random(seek_pos)
        status_code = 206
    else:
        manage.reload_settings()
        status_code = 200

    filename = manage.get_video_title()
    filename = filename.encode("utf-8", "ignore")
    video_size = manage.get_video_size()
    video_type = manage.get_video_ext()

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
                              content_type="text/html")