from django.shortcuts import render
from django.core.serializers.json import DjangoJSONEncoder

from py2neo import cypher, neo4j
from taikonetwork.neo4j_settings import NEO4J_ROOT_URI, NEO4J_DB_URI

import random
import json
import string


def network_graph(request):
    return render(request, 'graph/network_graph.html')


def demographic_graph(request):
    config_json = demographic_graph_config()
    return render(request, 'graph/demographic_graph.html',
                  {'config_json': config_json})


def connection_graph(request):
    return render(request, 'graph/connection.html')


def degree_graph(request):
    return render(request, 'graph/degree.html')


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
        return None
    else:
        if tx.finished:
            return results
        else:
            return None


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


