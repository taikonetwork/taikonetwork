from django.conf.urls import patterns, url

from map import views

urlpatterns = patterns('',
    url(r'^$', views.globe, name='globe'),
    url(r'^groups/$', views.grouplist, name='grouplist'),
)
