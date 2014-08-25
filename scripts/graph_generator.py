#!/usr/bin/env python
import random
import json


def generate_label():
    labels = ['Welcome', 'to', 'the', 'Taiko', 'Network']
    i = random.randint(0, 4)
    return labels[i]


def generate_color(s, v):
    golden_ratio_conjugate = 0.618033988749895
    h = random.random()  # use random start value
    h += golden_ratio_conjugate
    h %= 1
    r, g, b = hsv_to_rgb(h, s, v)
    return "rgba({}, {}, {}, ".format(r, g, b)


def hsv_to_rgb(h, s, v):
    h_i = int(h * 6)
    f = h * 6 - h_i
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)

    if h_i == 0:
        r, g, b = v, t, p
    elif h_i == 1:
        r, g, b = q, v, p
    elif h_i == 2:
        r, g, b = p, v, t
    elif h_i == 3:
        r, g, b = p, q, v
    elif h_i == 4:
        r, g, b = t, p, v
    elif h_i == 5:
        r, g, b = v, p, q

    return int(r * 256), int(g * 256), int(b * 256)


def create_graph():
    num_clusters = 5
    num_nodes = 500
    # cluster_colors = [generate_color(0.5, 0.95) for i in range(num_clusters)]
    cluster_colors = ["rgba(164, 243, 121, ",
                      "rgba(243, 230, 121, ",
                      "rgba(243, 121, 184, ",
                      "rgba(154, 121, 243, ",
                      "rgba(121, 194, 243, "]

    nodes = []
    for i in range(num_nodes):
        cluster_color = cluster_colors[i % num_clusters] + '1)'
        node = {'id': str(i),
                'label': generate_label(),
                'size': 5.0 + random.randrange(20.0),
                'color': cluster_color,
                'x': random.randrange(600) - 300,
                'y': random.randrange(150) - 150}
        nodes.append(node)

    edges = []
    id = 0
    for start in range(num_nodes):
        members = [x * 10 + (start % num_clusters) for x in range(20)]
        try:
            members.remove(start)
        except ValueError:
            pass

        edge_color = cluster_colors[start % num_clusters] + '0.3)'

        used_members = random.sample(members, 3)
        for end in used_members:
            if not start == end:
                edge = {'id': str(id),
                        'source': str(start),
                        'target': str(end),
                        'color': edge_color,
                        'type': 'curve'}
                edges.append(edge)
                id += 1

        for i in range(3):
            end = random.randrange(num_nodes)
            if not start == end and end not in used_members:
                edge = {'id': str(id),
                        'source': str(start),
                        'target': str(end),
                        'color': edge_color,
                        'type': 'curve'}
                edges.append(edge)
                id += 1

    print(id)
    graph = {'nodes': nodes, 'edges': edges}
    json_file = open('taikonetwork.json', 'w')
    json.dump(graph, json_file)
    json_file.close()


if __name__ == '__main__':
    create_graph()
