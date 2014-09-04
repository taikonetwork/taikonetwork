from django.shortcuts import render
from django.core.serializers.json import DjangoJSONEncoder

from py2neo import cypher, neo4j
from taikonetwork.neo4j_settings import NEO4J_ROOT_URI, NEO4J_DB_URI

import random
import json


def network_graph(request):
    graph_json = query_entire_network()

    return render(request, 'graph/network_graph.html',
                  {'graph_json': graph_json})


def demographic_graph(request):
    graph_json = query_entire_network()
    colors_json = demographic_group_colors()

    return render(request, 'graph/demographic_graph.html',
                  {'graph_json': graph_json, 'colors_json': colors_json})


def membership_graph(request):
    return render(request, 'graph/membership_graph.html')


def connections_graph(request):
    return render(request, 'graph/connections.html')


def degrees_graph(request):
    return render(request, 'graph/degrees.html')


# ----------------------------------------------------------
# Helper Methods
# ----------------------------------------------------------
def query_entire_network():
    graphdb = neo4j.GraphDatabaseService(NEO4J_DB_URI)
    nodes = get_all_member_nodes(graphdb)
    edges = get_unique_connections(graphdb)

    network_graph = {'nodes': nodes, 'edges': edges}
    graph_json = json.dumps(network_graph, cls=DjangoJSONEncoder)
    return graph_json


def get_all_member_nodes(graphdb):
    members = graphdb.find('Member')
    nodes = []

    for m in members:
        node_color = random_color(m._id) + '1)'
        properties = m.get_cached_properties()

        node = {'id': str(m._id),
                'label': properties['firstname'],
                'size': 5.0 + random.randrange(20.0),
                'color': node_color,
                'x': random.randrange(600) - 300,
                'y': random.randrange(150) - 150,
                'data': properties}
        nodes.append(node)

    return nodes


def get_unique_connections(graphdb):
    connections = graphdb.match(rel_type='CONNECTED_TO')
    edges = []
    unique_rels = []

    for c in connections:
        start = c.start_node._id
        end = c.end_node._id
        if (start, end) not in unique_rels and (end, start) not in unique_rels:
            edge_color = random_color(start) + '0.3)'
            edge = {'id': str(c._id),
                    'source': str(start),
                    'target': str(end),
                    'color': edge_color,
                    'type': 'curve'}
            edges.append(edge)
            unique_rels.append((start, end))

    return edges


def demographic_group_colors():
    gender_colors = {'Male': 'rgba(121, 182, 243, 1)',
                     'Female': 'rgba(243, 121, 203, 1)'}
    race_colors = {
        'American Indian or Alaska Native': 'rgba(243, 242, 121, 1)',
        'Asian or Asian American': 'rgba(243, 121, 238, 1)',
        'Pacific Islander or Native Hawaiian': 'rgba(121, 243, 212, 1)',
        'Black or African American': 'rgba(243, 177, 121, 1)',
        'White or Caucasian': 'rgba(112, 217, 108, 1)',
        'Hispanic or Latino': 'rgba(141, 121, 243, 1)'
    }
    asian_colors = {
        'Cambodian': 'rgba(202, 243, 121, 1)',
        'Chinese': 'rgba(2, 86, 253, 1)',
        'Filipino': 'rgba(243, 242, 121, 1)',
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
        'Vietnamese': 'rgba(121, 243, 212, 1)'
    }
    default_colors = ["rgba(164, 243, 121, 1)",
                      "rgba(243, 230, 121, 1)",
                      "rgba(243, 121, 184, 1)",
                      "rgba(154, 121, 243, 1)",
                      "rgba(121, 194, 243, 1)"]

    colors = {'gender': gender_colors, 'race': race_colors,
              'asian_ethnicity': asian_colors, 'default': default_colors}
    colors_json = json.dumps(colors, cls=DjangoJSONEncoder)
    return colors_json


def random_color(obj_id):
    colors = ["rgba(164, 243, 121, ",
              "rgba(243, 230, 121, ",
              "rgba(243, 121, 184, ",
              "rgba(154, 121, 243, ",
              "rgba(121, 194, 243, "]
    return colors[obj_id % 5]


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


def create_test_network(n, e):
    nodes = []
    gender = ['Male', 'Female', 'None']
    race = ['American Indian or Alaska Native', 'Asian or Asian American',
            'Pacific Islander or Native Hawaiian', 'Black or African American',
            'White or Caucasian', 'Hispanic or Latino', 'None']
    asian_ethnicity = ['Cambodian', 'Chinese', 'Filipino', 'Indian',
                       'Indonesian', 'Japanese', 'Javanese', 'Korean',
                       'Laotian', 'Malaysian', 'Mauritian', 'Okinawan',
                       'Palestinian', 'Syrian', 'Taiwanese', 'Thai',
                       'Vietnamese', 'None']

    for n_id in range(n):
        node_color = random_color(n_id) + '1)'
        dob = '{}-{}-{}'.format(random.randint(1950, 2008),
                                random.randint(1, 12),
                                random.randint(1, 28))
        properties = {'sf_id': '000i123000000UVxyzASDF',
                      'firstname': 'TestFirstname',
                      'lastname': 'TestLastname',
                      'race': race[n_id % 7],
                      'asian_ethnicity': asian_ethnicity[n_id % 18],
                      'gender': gender[n_id % 3],
                      'dob': dob}
        node = {'id': str(n_id),
                'label': properties['firstname'],
                'size': 3.0,
                'color': node_color,
                'x': random.randrange(600) - 300,
                'y': random.randrange(150) - 150,
                'data': properties}
        nodes.append(node)

    edges = []
    unique_rels = []
    e_id = 0
    while e_id < e:
        start = random.randrange(n)
        end = random.randrange(n)
        if (not start == end and (start, end) not in unique_rels
                and (end, start) not in unique_rels):
            edge_color = random_color(start) + '0.3)'
            edge = {'id': str(e_id),
                    'source': str(start),
                    'target': str(end),
                    'color': edge_color,
                    'type': 'curve'}
            edges.append(edge)
            unique_rels.append((start, end))
            e_id += 1

    network = {'nodes': nodes, 'edges': edges}
    graph_json = json.dumps(network, cls=DjangoJSONEncoder)
    return graph_json
