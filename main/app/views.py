# Create your views here.
from django.http import HttpResponse

# --------------------------------------------------------------------------------------
def streamLoader( request ):
	manage = request.manage
	videoManager = manage.videoManager
	querystr = request.GET
	
	seekpos = querystr.get("start",0)
	
	try: seekpos = long( seekpos )
	except: seekpos = videoManager.get_relative_mp4( seekpos )
	
	if seekpos > 0 and manage.videoManager.suportaSeekBar():
		manage.setRandomRead( seekpos )
		status_code = 206
	else:
		manage.reloadSettings()
		status_code = 200
	
	print status_code, seekpos, querystr
	
	streamer = manage.getStreamer()
	response = HttpResponse(streamer.get_chunks(), status = status_code)
	
	response["Content-Type"] = "video/%s" % videoManager.getVideoExt()
	response["Content-Length"] = manage.getVideoSize()
	response["Content-Transfer-Encoding"] = "binary"
	filename = videoManager.getTitle().encode("utf-8","ignore")
	response['Content-Disposition'] = 'attachment; filename=%s'%filename
	response["Accept-Ranges"] = "bytes"
	print response["Content-Type"]
	return response










