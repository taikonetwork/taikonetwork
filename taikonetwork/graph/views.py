from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder

from py2neo import cypher
from taikonetwork.neo4j_settings import NEO4J_ROOT_URI

import random
import json
import string


@login_required(login_url='/')
def network_graph(request):
    return render(request, 'graph/network_graph.html')


@login_required(login_url='/')
def demographic_graph(request):
    config_json = demographic_graph_config()
    return render(request, 'graph/demographic_graph.html',
                  {'config_json': config_json})


@login_required(login_url='/')
def connection_graph(request):
    return render(request, 'graph/connections.html')


def process_query(request):
    response_data = {}
    first1 = request.GET.get('first1', ' ').title()
    last1 = request.GET.get('last1', ' ').title()
    first2 = request.GET.get('first2', ' ').title()
    last2 = request.GET.get('last2', ' ').title()

    result = find_path(first1, last1, first2, last2)
    response_data['graph'] = result.get('graph', None)
    response_data['member1'] = result.get('member1', None)
    response_data['member2'] = result.get('member2', None)
    response_data['degrees'] = result.get('degrees', None)
    response_data['error_msg'] = result.get('error_msg', None)

    return HttpResponse(json.dumps(response_data),
                        content_type="application/json")


def find_path(first1, last1, first2, last2):
    path_str = ("MATCH p=shortestPath( "
                "(a:Member {{firstname: '{0}', lastname: '{1}'}})"
                "-[r:CONNECTED_TO*]-"
                "(b:Member {{firstname: '{2}', lastname: '{3}'}}) ) "
                "RETURN nodes(p), rels(p)")

    query = path_str.format(first1, last1, first2, last2)
    results = query_neo4j_db(query)

    if results[0]:
        nodes_json = []
        edges_json = []
        for result in results:
            nodes = result[0].values[0]
            edges = result[0].values[1]

            for n in nodes:
                data = n.get_cached_properties()
                color = 0
                if ((data['firstname'] == first1 and data['lastname'] == last1)
                        or (data['firstname'] == first2 and data['lastname'] == last2)):
                    color = 1

                node = {'id': data['sf_id'],
                        'label': data['firstname'] + ' ' + data['lastname'],
                        'color': color}
                nodes_json.append(node)

            for e in edges:
                data = e.get_cached_properties()
                edge = {'source': data['_a_id'],
                        'target': data['_b_id'],
                        'label': data['group']}
                edges_json.append(edge)

        graph = {'nodes': nodes_json, 'edges': edges_json}
        return {'graph': graph,
                'member1': '{} {}'.format(first1, last1),
                'member2': '{} {}'.format(first2, last2),
                'degrees': len(edges_json)}
    else:
        error_msg = "No path connecting <strong>{} {}</strong> and <strong>{} {}</strong> was found.".format(
            first1, last1, first2, last2)
        return {'error_msg': error_msg}


# def find_all_connections(request):
#     six_degrees_str = ("MATCH (m:Member {{firstname: '{0}', lastname: '{1}'}})"
#                        "-[r:CONNECTED_TO*..6]-(n:Member) RETURN DISTINCT n LIMIT 100")
#     children_str = ("MATCH (m:Member {{firstname: '{0}', lastname: '{1}'}})"
#                     "-[r:CONNECTED_TO]-(n:Member) RETURN n.firstname, n.lastname LIMIT 15")


# ----------------------------------------------------------
# Helper Methods
# ----------------------------------------------------------
def query_neo4j_db(query):
    session = cypher.Session(NEO4J_ROOT_URI)
    try:
        tx = session.create_transaction()
        tx.append(query)
        results = tx.commit()
    except cypher.TransactionError:
        return []
    else:
        if tx.finished:
            return results
        else:
            return []


def demographic_graph_config():
    gender_colors = {'Male': 'rgba(121, 182, 243, 1)',
                     'Female': 'rgba(243, 121, 203, 1)',
                     'None': 'rgba(138, 138, 138, 0.8)'}
    race_colors = {
        'American Indian or Alaska Native': 'rgba(253, 231, 2, 1)',
        'Asian or Asian American': 'rgba(243, 121, 238, 1)',
        'Pacific Islander or Native Hawaiian': 'rgba(121, 243, 212, 1)',
        'Black or African American': 'rgba(243, 177, 121, 1)',
        'White or Caucasian': 'rgba(112, 217, 108, 1)',
        'Hispanic or Latino': 'rgba(141, 121, 243, 1)',
        'None': 'rgba(138, 138, 138, 0.8)',
        'Multiracial': 'rgba(0, 0, 0, 0.8)'
    }
    ethnic_colors = {
        'Cambodian': 'rgba(202, 243, 121, 1)',
        'Chinese': 'rgba(2, 86, 253, 1)',
        'Filipino': 'rgba(253, 231, 2, 1)',
        'Indian': 'rgba(243, 177, 121, 1)',
        'Indonesian': 'rgba(141, 121, 243, 1)',
        'Japanese': 'rgba(255, 2, 97, 1)',
        'Javanese': 'rgba(253, 95, 2, 1)',
        'Korean': 'rgba(157, 2, 253, 1)',
        'Laotian': 'rgba(2, 253, 64, 1)',
        'Malaysian': 'rgba(112, 217, 108, 1)',
        'Mauritian': 'rgba(253, 95, 2, 1)',
        'Okinawan': 'rgba(243, 121, 238, 1)',
        'Palestinian': 'rgba(166, 66, 68, 1)',
        'Syrian': 'rgba(166, 139, 66, 1)',
        'Taiwanese': 'rgba(108, 175, 217, 1)',
        'Thai': 'rgba(66, 166, 68, 1)',
        'Vietnamese': 'rgba(121, 243, 212, 1)',
        'None': 'rgba(138, 138, 138, 0.8)',
        'Multiethnic': 'rgba(0, 0, 0, 0.8)'
    }
    default_colors = ["rgba(164, 243, 121, 1)",
                      "rgba(243, 230, 121, 1)",
                      "rgba(243, 121, 184, 1)",
                      "rgba(154, 121, 243, 1)",
                      "rgba(202, 243, 121, 1)",
                      "rgba(243, 177, 121, 1)",
                      "rgba(243, 121, 238, 1)",
                      "rgba(121, 243, 212, 1)",
                      "rgba(243, 190, 121, 1)",
                      "rgba(2, 86, 253, 1)",
                      "rgba(255, 2, 97, 1)",
                      "rgba(157, 2, 253, 1)"]

    gender_cat = ['Male', 'Female']
    race_cat = ['American Indian or Alaska Native', 'Asian or Asian American',
                'Pacific Islander or Native Hawaiian', 'Black or African American',
                'White or Caucasian', 'Hispanic or Latino', 'Multiracial']
    ethnic_cat = ['Cambodian', 'Chinese', 'Filipino', 'Indian', 'Indonesian',
                  'Japanese', 'Javanese', 'Korean', 'Laotian', 'Malaysian',
                  'Mauritian', 'Okinawan', 'Palestinian', 'Syrian', 'Taiwanese',
                  'Thai', 'Vietnamese', 'Multiethnic']

    config = {'gender': {'colors': gender_colors, 'categories': gender_cat},
              'race': {'colors': race_colors, 'categories': race_cat},
              'ethnicity': {'colors': ethnic_colors, 'categories': ethnic_cat},
              'default': {'colors': default_colors}}

    config_json = json.dumps(config, cls=DjangoJSONEncoder)
    return config_json


# ----------------------------------------------------------
# TESTING METHODS
# ----------------------------------------------------------
def create_test_network(n, e):
    nodes = []
    gender = ['Male', 'Female', 'None']
    race = ['American Indian or Alaska Native', 'Asian or Asian American',
            'Pacific Islander or Native Hawaiian', 'Black or African American',
            'White or Caucasian', 'Hispanic or Latino', 'None', 'Multiple']
    ethnicity = ['Cambodian', 'Chinese', 'Filipino', 'Indian',
                 'Indonesian', 'Japanese', 'Javanese', 'Korean',
                 'Laotian', 'Malaysian', 'Mauritian', 'Okinawan',
                 'Palestinian', 'Syrian', 'Taiwanese', 'Thai',
                 'Vietnamese', 'None', 'Multiple']

    for n_id in range(n):
        node_color = random_color(n_id, 1)
        dob = '{}-{}-{}'.format(random.randint(1950, 2008),
                                random.randint(1, 12),
                                random.randint(1, 28))
        sf_id = 'id000' + ''.join(random.choice(
            string.ascii_uppercase + string.ascii_lowercase +
            string.digits) for _ in range(20))
        gen_name = lambda x: 'NN' + random.choice(
            string.ascii_uppercase) + ''.join(random.choice(
                string.ascii_lowercase) for _ in range(x))

        properties = {'sf_id': sf_id,
                      'firstname': gen_name(8),
                      'lastname': gen_name(11),
                      'race': race[n_id % 8],
                      'ethnicity': ethnicity[n_id % 19],
                      'gender': gender[n_id % 3],
                      'dob': dob}
        node = {'id': str(n_id),
                'label': properties['firstname'] + ' ' + properties['lastname'],
                'color': node_color,
                'attributes': properties}
        nodes.append(node)

    edges = []
    unique_rels = []
    e_id = 0
    while e_id < e:
        start = random.randrange(n)
        end = random.randrange(n)
        if (not start == end and (start, end) not in unique_rels
                and (end, start) not in unique_rels):
            edge_color = random_color(start, 0.3)
            edge = {'id': str(e_id),
                    'source': str(start),
                    'target': str(end),
                    'color': edge_color}
            edges.append(edge)
            unique_rels.append((start, end))
            e_id += 1

    network = {'nodes': nodes, 'edges': edges}
    graph_json = json.dumps(network, cls=DjangoJSONEncoder)
    return graph_json


def random_color(obj_id, alpha):
    colors = ["rgba(164, 243, 121, ",
              "rgba(243, 230, 121, ",
              "rgba(243, 121, 184, ",
              "rgba(154, 121, 243, ",
              "rgba(202, 243, 121, ",
              "rgba(243, 177, 121, ",
              "rgba(243, 121, 238, ",
              "rgba(121, 243, 212, ",
              "rgba(243, 190, 121, ",
              "rgba(2, 86, 253, ",
              "rgba(255, 2, 97, ",
              "rgba(157, 2, 253, "]

    return colors[obj_id % 12] + str(alpha) + ')'
