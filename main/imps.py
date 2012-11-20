from django.template import Context, Template, loader, defaulttags, defaultfilters, loader_tags
from django.contrib.messages.storage import fallback
from django.core.mail.backends import smtp
import xml.etree.ElementTree
from main.app import browser
from main.app import generators
