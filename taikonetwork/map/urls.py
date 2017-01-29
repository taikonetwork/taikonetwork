from django.conf.urls import patterns, url

from map import views

urlpatterns = patterns('',
    url(r'^$', views.groupmap, name='groupmap'),
    url(r'^groups/$', views.grouplist, name='grouplist'),
    url(r'^query-members/$', views.query_members, name='query_members'),
)
