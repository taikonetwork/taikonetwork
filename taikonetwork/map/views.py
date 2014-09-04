from django.shortcuts import render
from django.core.serializers.json import DjangoJSONEncoder

from datahandler.models import Group
import json


def groupmap(request):
    return render(request, 'map/groupmap.html')


def grouplist(request):
    taiko_groups = Group.objects.filter(accounttype='Taiko Group')
    groups_formatted = []
    for g in taiko_groups:
        year = None
        if g.founding_date:
            year = g.founding_date.year
        groups_formatted.append({'name': g.name, 'category': g.category,
                                 'year': year, 'country': g.country,
                                 'state': g.state, 'city': g.city})

    groups_json = json.dumps(groups_formatted, cls=DjangoJSONEncoder)
    return render(request, 'map/grouplist.html', {'groups_json': groups_json})
