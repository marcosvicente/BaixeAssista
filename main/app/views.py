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
		statuscode = 206
	else:
		manage.reloadSettings()
		statuscode = 200
	
	seekpos = long(seekpos)
	print statuscode, seekpos, querystr
	
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










