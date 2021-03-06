from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()

import home.views

urlpatterns = patterns('',
    url(r'^$', home.views.index, name='index'),
    url(r'^about/', home.views.about, name='about'),
    url(r'^login/', home.views.login_form, name='login'),
    url(r'^map/', include('map.urls')),
    url(r'^graphs/', include('graph.urls')),
    url(r'^metrics/', include('metrics.urls')),

    url(r'^admin/', include(admin.site.urls)),
)
