from django.shortcuts import render
from django.http import HttpResponse
from django.core.cache import cache
from django.contrib.auth.decorators import login_required

import json
from graph import helper


@login_required(login_url='/')
def network_graph(request):
    return render(request, 'graph/network_graph.html')


@login_required(login_url='/')
def demographic_graph(request):
    config_json = helper.configure_demographic_graph()
    return render(request, 'graph/demographic_graph.html',
                  {'config_json': config_json})


@login_required(login_url='/')
def connection_graph(request):
    return render(request, 'graph/connections.html')


def process_connection_query(request):
    first1 = request.GET.get('first1', ' ').title()
    last1 = request.GET.get('last1', ' ').title()
    first2 = request.GET.get('first2', ' ').title()
    last2 = request.GET.get('last2', ' ').title()

    cache_key = 'graph_connection:{0}_{1}_{2}_{3}'.format(first1, last1, first2, last2)
    # Store in cache for 1 week (in seconds).
    cache_timeout = 604800

    result = cache.get(cache_key)
    if not result:
        result = helper.find_shortest_path(first1, last1, first2, last2)
        if not result.get('error_msg', None):
            cache.set(cache_key, result, cache_timeout)

    return HttpResponse(json.dumps(result),
                        content_type="application/json")
