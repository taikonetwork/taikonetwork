"""
    datahandler.util.neo4j_cypher
    -------------------------------

    Cypher query statements for synchronizing Neo4j database.

"""

# For GROUP nodes:
GROUP_DELETE_QUERY = ('MATCH (node:Group {{ sf_id: "{sf_id}" }}) '
                      'OPTIONAL MATCH (node)-[rel]-() '
                      'DELETE node, rel RETURN count(node)')
GROUP_MERGE_QUERY = ('MERGE (node:Group {{ sf_id: "{0}" }}) '
                     'ON CREATE SET node.name = "{1}" '
                     'ON MATCH SET node.name = "{1}" '
                     'RETURN count(node)')

# For MEMBER nodes:
MEMBER_DELETE_QUERY = ('MATCH (node:Member {{ sf_id: "{sf_id}" }}) '
                       'OPTIONAL MATCH (node)-[rel]-() '
                       'DELETE node, rel RETURN count(node)')
MEMBER_MERGE_QUERY = ('MERGE (node:Member {{ sf_id: "{0}" }}) '
                      'ON CREATE SET node += {{ '
                      'firstname: "{1}", '
                      'lastname: "{2}", '
                      'dob: "{3}", '
                      'gender: "{4}", '
                      'race: "{5}", '
                      'asian_ethnicity: "{6}" }}'
                      'ON MATCH SET node += {{ '
                      'firstname: "{1}", '
                      'lastname: "{2}", '
                      'dob: "{3}", '
                      'gender: "{4}", '
                      'race: "{5}", '
                      'asian_ethnicity: "{6}" }} '
                      'RETURN count(node)')

# For MEMBERSHIP relationships:
MEMBERSHIP_DELETE_QUERY = ('MATCH (m:Member)-[rel:MEMBER_OF]->(g:Group) '
                           'WHERE rel.sf_id = "{sf_id}" '
                           'DELETE rel RETURN count(rel)')
MEMBERSHIP_MERGE_QUERY = ('MATCH (m:Member {{ sf_id: "{member_id}" }}),'
                          '(g:Group {{ sf_id: "{group_id}" }}) '
                          'MERGE (m)-[rel:MEMBER_OF '
                          '{{ sf_id: "{mship_id}" }}]->(g) '
                          'ON CREATE SET rel += {{ '
                          'status: "{status}", '
                          'start: toInt({start}), '
                          'end: toInt({end}), '
                          '_is_new: true }} '
                          'ON MATCH SET rel += {{ '
                          'status: "{status}", '
                          'start: toInt({start}), '
                          'end: toInt({end}), '
                          '_is_new: false }} '
                          'RETURN count(rel)')

# For CONNECTION relationships:
CONNECTION_GET_QUERY = ('MATCH (a:Member {{sf_id: "{a_id}" }})-[c:CONNECTED_TO '
                        '{{_group_id: "{group_id}" }}]-(b:Member) '
                        'WHERE c._a_mship = "{mship_id}" '
                        'OR c._b_mship = "{mship_id}" '
                        'RETURN c')

CONNECTION_ADD_QUERY = ('MATCH (a:Member '
                        '{{sf_id: "{a_id}" }})-[r1:MEMBER_OF {{sf_id: '
                        '"{mship_id}"}}]->(g:Group {{sf_id: "{group_id}"}}), '
                        '(b:Member)-[r2:MEMBER_OF]->(g:Group '
                        '{{sf_id: "{group_id}"}}) '
                        'WHERE NOT a = b AND r1.start <= r2.end '
                        'AND r2.start <= r1.end '
                        'MERGE (a)-[c:CONNECTED_TO {{_group_id: g.sf_id}}]-(b) '
                        'ON CREATE SET c += {{ '
                        'group: g.name, '
                        '_a_id: a.sf_id, '
                        '_a_mship: r1.sf_id, '
                        '_a_start: r1.start, '
                        '_a_end: r1.end, '
                        '_b_id: b.sf_id, '
                        '_b_mship: r2.sf_id, '
                        '_b_start: r2.start, '
                        '_b_end: r2.end }} '
                        'RETURN count(c)')

CONNECTION_DELETE_QUERY = ('MATCH (a:Member {{sf_id: "{m_id}" }})-'
                           '[c:CONNECTED_TO {{_group_id: "{group_id}"}}]-(b:Member) '
                           'WHERE c._a_mship = "{mship_id}" '
                           'OR c._b_mship = "{mship_id}" '
                           'DELETE c RETURN count(c)')

CONNECTION_UPDATE_QUERY = ('MATCH (a:Member {{sf_id: "{m_id}" }})-'
                           '[c:CONNECTED_TO {{_group_id: "{group_id}", '
                           '{mship_label}: "{mship_id}"}}]-(b:Member) '
                           'SET c += {{ '
                           '{id_label}: "{m_id}", '
                           '{start_label}: {m_start}, '
                           '{end_label}: {m_end} }} '
                           'RETURN count(c)')

############################################################
# Neo4j database models (not managed; for reference)
############################################################
"""
# Label = 'Group'
class Group(Node):
    element_type = 'Group'

    sf_id = String(nullable=False)
    name = String(nullable=False)

# Label = 'Member'
class Member(Node):
    element_type = 'Member'

    sf_id = String(nullable=False)
    firstname = String(nullable=False)
    lastname = String(nullable=False)
    dob = Date()
    gender = String()
    race = String()
    asian_ethnicity = String()

class Membership(Relationship):
    label = 'MEMBER_OF'

    sf_id = String(nullable=False)
    status = String()
    start = Integer()
    end = Integer()
    _is_new = Boolean()

class Connection(Relationship):
    label = 'CONNECTED_TO'

    group = String(nullable=False)
    _a_id = String()
    _a_start = Integer()
    _b_end = Integer()
    _b_id = String()
    _b_start = Integer()
    _b_end = Integer()
"""
