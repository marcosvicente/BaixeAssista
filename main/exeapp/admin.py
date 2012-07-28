from django.contrib.admin import site
from models import Url, Browser, Resume

try: site.register( Url )
except: pass
try: site.register( Browser )
except: pass
try: site.register( Resume )
except: pass 