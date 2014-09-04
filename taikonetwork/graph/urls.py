from django.conf.urls import patterns, url

from graph import views

urlpatterns = patterns('',
    url(r'^network/$', views.network_graph, name='network_graph'),
    url(r'^demographic/$', views.demographic_graph, name='demographic_graph'),
    url(r'^membership/$', views.membership_graph, name='membership_graph'),
    url(r'^connections/$', views.connections_graph, name='connections_graph'),
    url(r'^degrees/$', views.degrees_graph, name='degrees_graph'),
)
