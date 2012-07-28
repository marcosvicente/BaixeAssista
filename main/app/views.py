# Create your views here.

from django.http import HttpResponse
import models

def show_data(request):
	d = '\n'.join(["- " + m.title for m in models.Url.objects.all()])
	return HttpResponse( d, "txt" )

def show_token(request):
	return HttpResponse("TOKEN: %s UID: %s"%(request.GET.get("oauth_token",None), request.GET.get("uid", None)))