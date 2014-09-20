############################################################
# graph_exporter.py
# ---------------
# Pulls graph data from Neo4J database, creates a NetworkX
# graph object, and then writes it to file in specified format.
# *** For querying large graph dataset (entire network). ***
#
############################################################
from django.core.serializers.json import DjangoJSONEncoder
from py2neo import neo4j
from taikonetwork.neo4j_settings import NEO4J_DB_URI
import networkx as nx
import json


class GraphExporter:
    def __init__(self):
        self.Graph = nx.Graph()

    def query_taikonetwork_graph(self):
        self.neo4jdb = neo4j.GraphDatabaseService(NEO4J_DB_URI)
        self._add_group_nodes()
        self._add_memberships()
        self._add_member_nodes()
        self._add_unique_connections()

    def query_demographic_graph(self):
        self.neo4jdb = neo4j.GraphDatabaseService(NEO4J_DB_URI)
        self._add_member_nodes(demo=True)
        self._add_unique_connections(demo=True)

    def export_gexf_graph(self, filepath='graph.gexf'):
        nx.write_gexf(self.Graph, filepath,
                      encoding='utf-8', prettyprint=True, version='1.2draft')

    def export_json_graph(self, filepath='graph.json'):
        json_data = nx.readwrite.json_graph(self.G)
        with open(filepath, 'w') as fp:
            json.dump(json_data, fp, cls=DjangoJSONEncoder)

    def _add_group_nodes(self):
        groups = self.neo4jdb.find('Group')
        color = {'r': 255, 'g': 2, 'b': 97, 'a': 1}

        for g in groups:
            data = g.get_cached_properties()
            self.Graph.add_node(
                g._id, label=data['name'], sf_id=data['sf_id'],
                viz={'color': color})

    def _add_member_nodes(self, demo=False):
        members = self.neo4jdb.find('Member')

        for m in members:
            data = m.get_cached_properties()
            color = self._random_color(m._id, 1)
            if demo:
                self.Graph.add_node(
                    m._id, label=data['firstname'] + ' ' + data['lastname'],
                    gender=data['gender'], dob=data['dob'],
                    race=data['race'], ethnicity=data['asian_ethnicity'],
                    viz={'color': color})
            else:
                self.Graph.add_node(
                    m._id, label=data['firstname'] + ' ' + data['lastname'],
                    sf_id=data['sf_id'],
                    viz={'color': color})

    def _add_unique_connections(self, demo=False):
        connections = self.neo4jdb.match(rel_type='CONNECTED_TO')
        unique_rels = []

        for c in connections:
            start = c.start_node._id
            end = c.end_node._id
            if (start, end) not in unique_rels and (end, start) not in unique_rels:
                if demo:
                    color = {'r': 213, 'g': 213, 'b': 213, 'a': 0.3}
                else:
                    color = self._random_color(start, 0.3)
                self.Graph.add_edge(start, end, viz={'color': color})
                unique_rels.append((start, end))

    def _add_memberships(self):
        memberships = self.neo4jdb.match(rel_type='MEMBER_OF')

        for ms in memberships:
            color = self._random_color(ms.start_node._id, 0.3)
            self.Graph.add_edge(ms.start_node._id, ms.end_node._id,
                                viz={'color': color})

    def _random_color(self, obj_id, alpha):
        colors = [{'r': 164, 'g': 243, 'b': 121},
                  {'r': 243, 'g': 230, 'b': 121},
                  {'r': 243, 'g': 121, 'b': 184},
                  {'r': 154, 'g': 121, 'b': 243},
                  {'r': 202, 'g': 243, 'b': 121},
                  {'r': 243, 'g': 177, 'b': 121},
                  {'r': 243, 'g': 121, 'b': 238},
                  {'r': 121, 'g': 243, 'b': 212},
                  {'r': 243, 'g': 190, 'b': 121},
                  {'r': 121, 'g': 194, 'b': 243},
                  {'r': 157, 'g': 2, 'b': 253},
                  {'r': 2, 'g': 86, 'b': 253}]

        c = colors[obj_id % 12]
        c['a'] = alpha
        return c
