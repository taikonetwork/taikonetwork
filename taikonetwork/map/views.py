from django.shortcuts import render
from django.http import HttpResponse
from django.core.serializers.json import DjangoJSONEncoder

from datahandler.models import GroupAlt
import json
from datetime import datetime
from py2neo import cypher
from taikonetwork.neo4j_settings import NEO4J_ROOT_URI


def groupmap(request):
    taiko_groups = GroupAlt.objects.filter(accounttype='Taiko Group')
    groups_filtered = []
    num_no_loc = 0
    for g in taiko_groups:
        if g.latitude and g.longitude:
            year = None
            if g.founding_date:
                year = g.founding_date.year

            group = {'name': g.name, 'sf_id': g.sf_id, 'year': year,
                     'lng': g.longitude, 'lat': g.latitude}
            groups_filtered.append(group)
        else:
            num_no_loc += 1

    groups_json = json.dumps(groups_filtered, cls=DjangoJSONEncoder)
    return render(request, 'map/groupmap.html', {'groups_json': groups_json,
                                                 'num_no_loc': num_no_loc})


def grouplist(request):
    taiko_groups = GroupAlt.objects.filter(accounttype='Taiko Group')
    groups_filtered = []
    for g in taiko_groups:
        year = None
        if g.founding_date:
            year = g.founding_date.year

        groups_filtered.append({'name': g.name, 'category': g.category,
                                'website': g.website,
                                'year': year, 'country': g.country,
                                'state': g.state, 'city': g.city})

    groups_json = json.dumps(groups_filtered, cls=DjangoJSONEncoder)
    return render(request, 'map/grouplist.html', {'groups_json': groups_json})


def query_members(request):
    query_str = ('MATCH (m:Member)-[r:MEMBER_OF]->'
                 '(g:Group {{ name: "{group}", sf_id: "{sf_id}" }}) '
                 'WHERE r.start <= toInt("{end_year}") '
                 'RETURN m.firstname + " " + m.lastname, r.start, r.end;')
    group = request.GET.get('group', '')
    sf_id = request.GET.get('sf_id', '')
    end_year = request.GET.get('end_year', '')
    query = query_str.format(group=group, sf_id=sf_id, end_year=end_year)

    try:
        session = cypher.Session(NEO4J_ROOT_URI)
        tx = session.create_transaction()
        tx.append(query)

        # Execute all queries on server and commit transaction.
        result = tx.commit()
    except cypher.TransactionError as error:
        return HttpResponse({'status': 'error', 'msg': str(error)})
    else:
        if tx.finished:
            members = []
            if len(result[0]) > 0:
                for m in result[0]:
                    start = m[1]
                    end = m[2]
                    current = datetime.now().year
                    if start == 9999:
                        start = current
                    if end == 9999:
                        end = current
                    year = start
                    if start != end:
                        year = '{} - {}'.format(start, end)
                    members.append({'name': m[0], 'active_years': year})

            response = json.dumps({'status': 'ok', 'members': members, 'query': query}, cls=DjangoJSONEncoder)
            return HttpResponse(response, content_type="application/json")
        else:
            return HttpResponse({'status': 'error', 'msg':
                                           'NEO4J ERROR: Transaction not finished.'})
