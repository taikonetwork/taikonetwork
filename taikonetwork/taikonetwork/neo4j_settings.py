"""
neo4j_settings.py
-------------------
Configurations for remote Neo4j database.

"""

NEO4J_ROOT_URI = 'http://ec2-54-191-63-134.us-west-2.compute.amazonaws.com:7474'
NEO4J_DB_URI = 'http://ec2-54-191-63-134.us-west-2.compute.amazonaws.com:7474/db/data/'


# Neo4j database models (not managed; for reference)
"""
# Label = 'Group'
class Group(Node):
    element_type = 'group'

    sf_id = String(nullable=False)
    name = String(nullable=False)

# Label = 'Member'
class Member(Node):
    element_type = 'member'

    sf_id = String(nullable=False)
    firstname = String(nullable=False)
    lastname = String(nullable=False)
    dob = Date()
    gender = String()
    race = String()
    asian_ethnicity = String()

class Membership(Relationship):
    label = 'member_of'

    sf_id = String(nullable=False)
    status = String()
    start = Integer()
    end = Integer()
    _is_new = Boolean()

class Connection(Relationship):
    label = 'connected_to'

    group = String(nullable=False)
    _a_id = String()
    _a_start = Integer()
    _b_end = Integer()
    _b_id = String()
    _b_start = Integer()
    _b_end = Integer()
"""
