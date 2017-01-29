from django.conf.urls import patterns, url

from metrics import views

urlpatterns = patterns('',
    url(r'^$', views.display_metrics, name='metrics'),
)
