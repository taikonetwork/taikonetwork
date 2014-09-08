from django.conf.urls import patterns, url

from graph import views

urlpatterns = patterns('',
    url(r'^network/$', views.network_graph, name='network_graph'),
    url(r'^demographic/$', views.demographic_graph, name='demographic_graph'),
    url(r'^membership/$', views.membership_graph, name='membership_graph'),
    url(r'^connection/$', views.connection_graph, name='connection_graph'),
    url(r'^degree/$', views.degree_graph, name='degree_graph'),
)
