##################################################################
# _neo4j_updater.py
# ------------------
# Methods for syncing NEO4J nodes and relationships via
# Cypher transactions.
#
##################################################################
from py2neo import cypher
from taikonetwork.neo4j_settings import NEO4J_ROOT_URI


class Neo4jUpdater:
    def __init__(self):
        """Connect session using root service uri for Cypher transactions."""
        self.session = cypher.Session(NEO4J_ROOT_URI)

    def update_node_groups(self, groups):
        merge_cypher = ('MERGE (node:Group {{ sf_id: "{sf_id}" }}) '
                        'ON CREATE SET node.name = "{name}" '
                        'RETURN count(node)')
        delete_cypher = ('MATCH (node:Group {{ sf_id: "{sf_id}" }})-[rel]-() '
                         'DELETE node, rel')

        try:
            tx = self.session.create_transaction()
            num_removed = 0

            for g in groups:
                if g['is_deleted']:
                    print("> REMOVED 'Group' node: {0}".format(
                        g['name']))
                    num_removed += 1
                    query = delete_cypher.format(sf_id=g['Id'])
                else:
                    # Update or create if none exist.
                    query = merge_cypher.format(sf_id=g['Id'], name=g['name'])
                tx.append(query)

            # Execute all queries on server and commit transaction.
            group_nodes = tx.commit()
        except cypher.TransactionError as error:
            err_msg = ('! --- TRANSACTION ERROR --- !\n' + str(error))
            return (False, err_msg)
        else:
            if tx.finished:
                num_results = len(group_nodes)
                # Nested empty lists returned when no query matches or updates.
                if num_results == 1:
                    num_results = len(group_nodes[0])

                status_msg = (">>> [{0}] 'Group' node(s) successfully "
                              "synced.".format(num_results))
                if num_removed:
                    status_msg += ("\n>>> [{0}] 'Group' node(s) removed.".format(
                        num_removed))

                return (True, status_msg)
            else:
                err_msg = ("! --- TRANSACTION ERROR --- !\n"
                           "Transaction for 'Group' nodes not finished.")
                return (False, err_msg)

    def update_node_members(self, members):
        merge_cypher = ('MERGE (node:Member {{ sf_id: "{sf_id}" }}) '
                        'ON CREATE SET node += {{ '
                        'firstname: "{firstname}", '
                        'lastname: "{lastname}", '
                        'dob: "{dob}", '
                        'gender: "{gender}", '
                        'race: "{race}", '
                        'asian_ethnicity: "{asian_ethnicity}" }}'
                        'ON MATCH SET node += {{ '
                        'firstname: "{firstname}", '
                        'lastname: "{lastname}", '
                        'dob: "{dob}", '
                        'gender: "{gender}", '
                        'race: "{race}", '
                        'asian_ethnicity: "{asian_ethnicity}" }} '
                        'RETURN count(node)')
        delete_cypher = ('MATCH (node:Member {{ sf_id: "{sf_id}" }})-[rel]-() '
                         'DELETE node, rel')

        try:
            tx = self.session.create_transaction()
            num_removed = 0

            for m in members:
                if m['is_deleted']:
                    print("> REMOVED 'Member' node: {0}".format(
                        m['Id']))
                    num_removed += 1
                    query = delete_cypher.format(sf_id=m['Id'])
                else:
                    # Update or create if none exists.
                    query = merge_cypher.format(sf_id=m['Id'],
                                                firstname=m['firstname'],
                                                lastname=m['lastname'],
                                                dob=m['dob'], race=m['race'],
                                                gender=m['gender'],
                                                asian_ethnicity=m['asian_ethnicity'])
                tx.append(query)

            # Execute all queries on server and commit transaction.
            member_nodes = tx.commit()
        except cypher.TransactionError as error:
            err_msg = ('! --- TRANSACTION ERROR --- !\n' + str(error))
            return (False, err_msg)
        else:
            if tx.finished:
                num_results = len(member_nodes)
                # Nested empty lists returned when no query matches or updates.
                if num_results == 1:
                    num_results = len(member_nodes[0])

                status_msg = (">>> [{0}] 'Member' node(s) successfully "
                              "synced.".format(num_results))
                if num_removed:
                    status_msg += (">>> [{0}] 'Member' node(s) "
                                   "removed.".format(num_removed))

                return (True, status_msg)
            else:
                err_msg = ("! --- TRANSACTION ERROR --- !\n"
                           "Transaction for 'Member' nodes not finished.")
                return (False, err_msg)

    def update_rel_memberships(self, memberships):
        merge_cypher = ('MATCH (m_node:Member {{ sf_id: "{member_id}" }}),'
                        '(g_node:Group {{ sf_id: "{group_id}" }}) '
                        'MERGE (m_node)-[rel:MEMBER_OF '
                        '{{ sf_id: "{mship_id}" }}]->(g_node) '
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
                        'RETURN rel')
        delete_cypher = ('MATCH (m:Member)-[rel:MEMBER_OF]->(g:Group) '
                         'WHERE rel.sf_id = "{sf_id}" '
                         'DELETE rel')

        try:
            tx = self.session.create_transaction()
            num_removed = 0

            # memberships is a dictonary of dictionaries, keyed by membership id
            for key, d in memberships.items():
                if d['is_deleted']:
                    print('! MEMBERSHIP_IS_DELETED: {0}'.format(key))
                    num_removed += 1
                    query = delete_cypher.format(sf_id=key)
                else:
                    # Update or create if none exists.
                    query = merge_cypher.format(member_id=d['member_id'],
                                                group_id=d['group_id'],
                                                mship_id=key,
                                                status=d['status'],
                                                start=d['start'],
                                                end=d['end'])
                tx.append(query)

            # Execute all queries on server and commit transaction.
            # Save results.
            self.membership_rels = tx.commit()
        except cypher.TransactionError as error:
            return (False, str(error))
        else:
            if tx.finished:
                num_results = len(self.membership_rels)
                # Nested empty lists returned when no query matches or updates.
                if num_results == 1:
                    num_results = len(self.membership_rels[0])

                return (True, num_results, num_removed)
            else:
                err_msg = ("Transaction for 'Membership' relationships not finished.")
                return (False, err_msg)

    def update_rel_connections(self, memberships):
        ret_cypher = ('MATCH (a:Member {{sf_id: "{a_id}" }})-[c:CONNECTED_TO '
                      '{{_group_id: "{group_id}" }}]-(b:Member) '
                      'WHERE c._a_mship = "{mship_id}" '
                      'OR c._b_mship = "{mship_id}" '
                      'RETURN c')

        new_cypher = ('MATCH (a:Member '
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

        update_cypher = ('MATCH (a:Member {{sf_id: "{m_id}" }})-'
                         '[c:CONNECTED_TO {{_group_id: "{group_id}", '
                         '{mship_label}: "{mship_id}"}}]-(b:Member) '
                         'SET c += {{ '
                         '{id_label}: "{m_id}", '
                         '{start_label}: {m_start}, '
                         '{end_label}: {m_end} }}')

        delete_cypher = ('MATCH (a:Member {{sf_id: "{m_id}" }})-'
                         '[c:CONNECTED_TO {{group_id: "{group_id}"}}]-(b:Member) '
                         'WHERE c._a_mship = "{mship_id}" '
                         'OR c._b_mship = "{mship_id}" '
                         'DELETE c')

        try:
            tx = self.session.create_transaction()
            num_removed = 0

            # Check which memberships were deleted, then
            # remove all related connections.
            for key, d in memberships.items():
                if d['is_deleted']:
                    print('! CONNECTION_IS_DELETED: {0}'.format(key))
                    num_removed += 1
                    query = delete_cypher.format(m_id=d['member_id'],
                                                 group_id=d['group_id'],
                                                 mship_id=key)
                    tx.append(query)

            # Iterate through newly-created/updated memberships and
            # update its corresponding connections.
            for membership_rel in self.membership_rels:
                # Get properties dict from Membership Relationship object.
                # This is a HACK for working with Record results from
                # cypher transactions. Due to wrong uri (localhost instead
                # of remote), connection is refused (unresolved bug in py2neo?).
                try:
                    rel = membership_rel[0][0]._properties
                except IndexError as error:
                    err_msg = ("{0}\n! --- PRINT OBJECT: {1}".format(
                        str(error), str(membership_rel)))
                    return (False, err_msg)

                d = memberships[rel['sf_id']]
                if rel['_is_new']:
                    # If newly-added membership relationship,
                    # create new connection relationships.
                    query = new_cypher.format(a_id=d['member_id'],
                                              group_id=d['group_id'],
                                              mship_id=rel['sf_id'])
                    tx.append(query)
                else:
                    # If modified and existing membership relationship,
                    # update/delete connection relationships.
                    # Get all connections related to specified membership.
                    ret_query = ret_cypher.format(a_id=d['member_id'],
                                                  group_id=d['group_id'],
                                                  mship_id=rel['sf_id'])
                    connections = self.session.execute(ret_query)

                    # For each connection relation, check if updated startyear
                    # endyear still overlap.
                    for connect in connections:
                        # HACK (see above): get properties dict from
                        # connection Relationship object.
                        try:
                            c = connect[0]._properties
                        except IndexError as error:
                            err_msg = ("{0}\n! --- PRINT OBJECT: {1}".format(
                                str(error), str(connect)))
                            return (False, err_msg)

                        # Determine which property member corresponds to,
                        # since connection relationship is undirected.
                        if d['member_id'] == c['_a_id']:
                            # Do nothing if dates were not changed.
                            if rel['start'] == c['_a_start'] and \
                               rel['end'] == c['_a_end']:
                                continue
                            else:
                                # Dates still overlap, so update.
                                if rel['start'] <= c['_b_end'] and \
                                   c['_b_start'] <= rel['end']:
                                    query = update_cypher.format(
                                        m_id=d['member_id'],
                                        group_id=d['group_id'],
                                        mship_label="_a_mship",
                                        mship_id=rel['sf_id'],
                                        id_label="_a_id",
                                        start_label="_a_start",
                                        end_label="_a_end",
                                        start=rel['start'],
                                        end=rel['end'])
                                else:
                                    # Dates no longer overlap, so remove.
                                    query = delete_cypher.format(
                                        m_id=d['member_id'],
                                        group_id=d['group_id'],
                                        mship_id=rel['sf_id'])

                        elif d['member_id'] == c['_b_id']:
                            if rel['start'] == c['_b_start'] and \
                               rel['end'] == c['_b_end']:
                                continue
                            else:
                                if rel['start'] <= c['_a_end'] and \
                                   c['_a_start'] <= rel['end']:
                                    query = update_cypher.format(
                                        m_id=d['member_id'],
                                        group_id=d['group_id'],
                                        mship_label="_b_mship",
                                        mship_id=rel['sf_id'],
                                        id_label="_b_id",
                                        start_label="_b_start",
                                        end_label="_b_end",
                                        start=rel['start'],
                                        end=rel['end'])
                                else:
                                    query = delete_cypher.format(
                                        m_id=d['member_id'],
                                        group_id=d['group_id'],
                                        mship_id=rel['sf_id'])

                        tx.append(query)

            connection_rels = tx.commit()
        except cypher.TransactionError as error:
            return (False, str(error))
        else:
            if tx.finished:
                num_results = len(connection_rels)
                # Nested empty lists returned when no query matches or updates.
                if num_results == 1:
                    num_results = len(connection_rels[0])

                return (True, num_results, num_removed)
            else:
                err_msg = ("Transaction for 'Membership' relationships not finished.")
                return (False, err_msg)
