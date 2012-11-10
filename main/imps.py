from django.template import Context, Template, loader, defaulttags, defaultfilters, loader_tags
from django.contrib.messages.storage import fallback
from django.core.mail.backends import smtp
from app.swfplayer import FlowPlayer, JWPlayer
from main.app.generators import *
import app.views
import app.admin
import app.browser
import app.manager
import app.window
import app.models
