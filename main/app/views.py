# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render_to_response
from main import settings
import urllib
import os
from django.template import Context, Template, loader

# --------------------------------------------------------------------------------------
def streamLoader( request ):
	if not request.manage:
		return HttpResponse("waiting...")
	
	manage = request.manage
	videoManager = manage.videoManager
	querystr = request.GET
	
	seekpos = querystr.get("start",0)
	
	try: seekpos = long( seekpos )
	except: seekpos = videoManager.get_relative_mp4( seekpos )
	
	if seekpos > 0 and manage.videoManager.suportaSeekBar():
		manage.setRandomRead( seekpos )
		statuscode = 206
	else:
		manage.reloadSettings()
		statuscode = 200
	
	seekpos = long(seekpos)
	filename = manage.getVideoTitle()
	filename = filename.encode("utf-8","ignore")
	videoSize = manage.getVideoSize()
	videoExt = manage.getVideoExt()
	
	response = HttpResponse(manage.get_streamer(), status = statuscode)
	response["Content-Type"] = "video/%s" %videoExt
	response["Content-Length"] = videoSize
	response["Content-Transfer-Encoding"] = "binary"
	response['Content-Disposition'] = 'attachment; filename=%s'%filename
	response["Accept-Ranges"] = "bytes"
	return response

def playerLoader(request):
	params = request.GET.copy()
	for key in params: params[key] = urllib.unquote_plus(params[key])
	return render_to_response(params["template"], {"params": params}, 
							  mimetype="text/html")







