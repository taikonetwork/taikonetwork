from django.shortcuts import render
from django.http import HttpResponse
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
    response_data = {}
    first1 = request.GET.get('first1', ' ').title()
    last1 = request.GET.get('last1', ' ').title()
    first2 = request.GET.get('first2', ' ').title()
    last2 = request.GET.get('last2', ' ').title()

    result = helper.find_shortest_path(first1, last1, first2, last2)
    response_data['paths'] = result.get('paths', None)
    response_data['member1'] = result.get('member1', None)
    response_data['member2'] = result.get('member2', None)
    response_data['degrees'] = result.get('degrees', None)
    response_data['error_msg'] = result.get('error_msg', None)

    return HttpResponse(json.dumps(response_data),
                        content_type="application/json")
