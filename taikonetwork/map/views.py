from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.core.cache import cache

import json
from datetime import datetime

from datahandler.models import Group


@login_required(login_url='/')
def groupmap(request):
    cache_key_json = 'map_groupmap_json'
    cache_key_count = 'map_groupmap_num_no_loc'
    # Store in cache for 1 week (in seconds)
    cache_timeout = 604800
    groups_json = cache.get(cache_key_json)
    num_no_loc = cache.get(cache_key_count)

    if not groups_json or not num_no_loc:
        taiko_groups = Group.objects.all()
        groups_filtered = []
        num_no_loc = 0
        for g in taiko_groups:
            if g.latitude and g.longitude:
                year = '----'
                if g.founding_date:
                    year = g.founding_date.year

                group_info = {}
                if g.website:
                    group_info['website'] = g.website
                if g.city or g.state or g.country:
                    location = '{0}, {1}, {2}'.format(g.city, g.state, g.country)
                    location = location.replace(' , ', ' ')
                    location = location.lstrip(', ')
                    location = location.rstrip(', ')
                    group_info['location'] = location

                group = {'name': g.name, 'sf_id': g.sf_id, 'year': year,
                         'lng': g.longitude, 'lat': g.latitude,
                         'info': group_info}
                groups_filtered.append(group)
            else:
                num_no_loc += 1

        groups_json = json.dumps(groups_filtered, cls=DjangoJSONEncoder)
        cache.set(cache_key_json, groups_json, cache_timeout)
        cache.set(cache_key_count, num_no_loc, cache_timeout)

    return render(request, 'map/groupmap.html', {'groups_json': groups_json,
                                                 'num_no_loc': num_no_loc})


@login_required(login_url='/')
def grouplist(request):
    cache_key = 'map_grouplist_json'
    # Store in cache for 1 week (in seconds)
    cache_timeout = 604800
    groups_json = cache.get(cache_key)

    if not groups_json:
        taiko_groups = Group.objects.all()
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
        cache.set(cache_key, groups_json, cache_timeout)

    return render(request, 'map/grouplist.html', {'groups_json': groups_json})


def query_members(request):
    group_name = request.GET.get('group', '')
    sf_id = request.GET.get('sf_id', '')
    end_year = request.GET.get('end_year', '')
    enddate = '{0}-12-31'.format(end_year)

    try:
        group = Group.objects.get(sf_id=sf_id, name=group_name)
        memberships = group.memberships.filter(startdate__lte=enddate)
    except Group.DoesNotExist:
        return HttpResponse({'status': 'error', 'msg': 'Taiko Group Not Found.'})

    members = []
    for mship in memberships:
        current = datetime.now().year
        start = mship.startdate.year
        if mship.enddate is None:
            if mship.status == 'Current':
                end = current
            else:
                end = start
        else:
            end = mship.enddate.year
        year = start
        if start != end:
            year = '{0} - {1}'.format(start, end)
        members.append({'name': mship.member.name, 'active_years': year})

    response = json.dumps({'status': 'ok', 'members': members}, cls=DjangoJSONEncoder)
    return HttpResponse(response, content_type="application/json")
