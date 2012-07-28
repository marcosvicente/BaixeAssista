from django.contrib.admin import site
from models import Url, Browser, Resume

site.register( Url )
site.register( Browser )
site.register( Resume )