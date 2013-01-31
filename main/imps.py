from django.template import Context, Template, loader, defaulttags, defaultfilters, loader_tags
from django.contrib.messages.storage import fallback
from django.core.mail.backends import smtp
from main.app import generators
import xml.etree.ElementTree

