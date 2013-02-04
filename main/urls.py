from django.conf.urls.defaults import patterns, include, url
from main import settings
from app import views

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    
    url(r'^static/(?P<path>.*)$', 'django.views.static.serve', 
                {'document_root': settings.STATIC_PATH, 'show_indexes': True}),
                       
    url(r'^stream/.+', views.streamLoader),
    url(r'^player/', views.playerLoader)
)
