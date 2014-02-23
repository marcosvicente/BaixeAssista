from django.conf.urls import patterns, include, url

from .app import views


# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from django.conf import settings

admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^admin/', include(admin.site.urls)),
                       url(r'^static/(?P<path>.*)$', 'django.views.static.serve',
                           {
                               'document_root': settings.STATIC_PATH,
                               'show_indexes': True
                           }
                       ),
                       url(r'^stream/.+', views.stream_loader),
                       url(r'^player/', views.player_loader, name='player-loader')
)
