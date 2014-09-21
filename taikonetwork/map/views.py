from django.shortcuts import render
from django.core.serializers.json import DjangoJSONEncoder

from datahandler.models import GroupAlt
import json


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
