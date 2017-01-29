# from django.test import TestCase
from datetime import date
import logging
from py2neo import authenticate, Graph
from taikonetwork.authentication import Neo4jAuth as neo4j
from datahandler.util import neo4j_cypher as cypher


logger = logging.getLogger('test')


class Neo4jUpdaterTest():
    def __init__(self):
        authenticate(neo4j.HOST_PORT, neo4j.USERNAME, neo4j.PASSWORD)
        self.graph = Graph(neo4j.REMOTE_URI)

        self.groups = [
            {'sf_id': 'sf_id_group_001', 'name': 'Taiko Group A'},
            {'sf_id': 'sf_id_group_002', 'name': 'Taiko Group B'},
            {'sf_id': 'sf_id_group_003', 'name': 'Taiko Group C'},
            {'sf_id': 'sf_id_group_004', 'name': 'Taiko Group D'},
            {'sf_id': 'sf_id_group_005', 'name': 'Taiko Group E'}
        ]
        self.members = [
            {'sf_id': 'sf_id_member_001',
             'firstname': 'Jane', 'lastname': 'Ro', 'dob': None,
             'gender': 'Female', 'race': 'Asian', 'asian_ethnicity': 'Japanese'
             },
            {'sf_id': 'sf_id_member_002',
             'firstname': 'John', 'lastname': 'Doe', 'dob': None,
             'gender': 'Male', 'race': 'White/Caucasian', 'asian_ethnicity': None
             }
        ]
        self.memberships = {
            'sf_id_mship_001': {
                'member_id': 'sf_id_member_001', 'group_id': 'sf_id_group_001',
                'status': 'Former', 'start': 1992, 'end': 1996
            },
            'sf_id_mship_002': {
                'member_id': 'sf_id_member_001', 'group_id': 'sf_id_group_002',
                'status': 'Former', 'start': 1997, 'end': 2001
            },
            'sf_id_mship_003': {
                'member_id': 'sf_id_member_001', 'group_id': 'sf_id_group_003',
                'status': 'Current', 'start': 2009, 'end': 9999
            },
            'sf_id_mship_004': {
                'member_id': 'sf_id_member_001', 'group_id': 'sf_id_group_004',
                'status': 'Former', 'start': 'null', 'end': 'null'
            },
            'sf_id_mship_005': {
                'member_id': 'sf_id_member_002', 'group_id': 'sf_id_group_001',
                'status': 'Former', 'start': 1992, 'end': 1996
            },
            'sf_id_mship_006': {
                'member_id': 'sf_id_member_002', 'group_id': 'sf_id_group_002',
                'status': 'Former', 'start': 1999, 'end': 2003
            },
            'sf_id_mship_007': {
                'member_id': 'sf_id_member_002', 'group_id': 'sf_id_group_003',
                'status': 'Former', 'start': 2005, 'end': 2013
            },
            'sf_id_mship_008': {
                'member_id': 'sf_id_member_002', 'group_id': 'sf_id_group_005',
                'status': 'Current', 'start': 9999, 'end': 9999
            }
        }

    def test_add_group_nodes(self):
        try:
            tx = self.graph.cypher.begin()
            for g in self.groups:
                query = cypher.GROUP_MERGE_QUERY.format(g['sf_id'], g['name'])
                tx.append(query)
                logger.debug("<Add GROUP>: {0}\n{1}\n".format(g['name'], query))
            results = tx.commit()
        except:
            logger.exception("<Add GROUP>: error encountered.")
            return False, None
        else:
            if tx.finished:
                logger.info("<Add GROUP>: SYNC OK.")
                return True, results
            else:
                logger.error("<Add GROUP>: transaction fail to commit.")
                return False, None

    def test_update_group_nodes(self):
        try:
            tx = self.graph.cypher.begin()
            for g in self.groups:
                query = cypher.GROUP_MERGE_QUERY.format(
                    g['sf_id'], 'UPDATED_{0}'.format(g['name']))
                tx.append(query)
                logger.debug("<Update GROUP>: {0}\n{1}\n".format(g['sf_id'], query))
            results = tx.commit()
        except:
            logger.exception("<Update GROUP>: error encountered.")
            return False, None
        else:
            if tx.finished:
                logger.info("Update GROUP>: SYNC OK.")
                return True, results
            else:
                logger.error("<Update GROUP>: transaction fail to commit.")
                return False, None

    def test_delete_group_nodes(self):
        try:
            tx = self.graph.cypher.begin()
            for g in self.groups:
                query = cypher.GROUP_DELETE_QUERY.format(sf_id=g['sf_id'])
                tx.append(query)
                logger.debug("<Delete GROUP>: {0}\n{1}\n".format(g['sf_id'], query))
            results = tx.commit()
        except:
            logger.exeception("<Delete GROUP>: error encountered.")
            return False, None
        else:
            if tx.finished:
                logger.info("<Delete GROUP>: SYNC OK.")
                return True, results
            else:
                logger.error("<Delete GROUP>: transaction fail to commit.")
                return False, None

    def test_add_member_nodes(self):
        try:
            tx = self.graph.cypher.begin()
            merge_fields = ['sf_id', 'firstname', 'lastname', 'dob', 'gender',
                            'race', 'asian_ethnicity']
            for m in self.members:
                values = [str(m[field]) for field in merge_fields]
                query = cypher.MEMBER_MERGE_QUERY.format(*values)
                tx.append(query)
                logger.debug("<Add MEMBER>: {0}\n{1}\n".format(m['sf_id'], query))
            results = tx.commit()
        except:
            logger.exception("<Add MEMBER>: error encountered.")
            return False, None
        else:
            if tx.finished:
                logger.info("<Add MEMBER>: SYNC OK.")
                return True, results
            else:
                logger.error("<Add MEMBER>: transaction fail to commit.")
                return False, None

    def test_update_member_nodes(self):
        try:
            tx = self.graph.cypher.begin()
            for m in self.members:
                query = cypher.MEMBER_MERGE_QUERY.format(
                    m['sf_id'], m['firstname'], m['lastname'], str(date.today()),
                    m['gender'], m['race'], m['asian_ethnicity'])
                tx.append(query)
                logger.debug("<Update MEMBER>: {0}\n{1}\n".format(m['sf_id'], query))
            results = tx.commit()
        except:
            logger.exception("<Update MEMBER>: error encountered.")
            return False, None
        else:
            if tx.finished:
                logger.info("<Update MEMBER>: SYNC OK.")
                return True, results
            else:
                logger.error("<Update MEMBER>: transaction fail to commit.")
                return False, None

    def test_delete_member_nodes(self):
        try:
            tx = self.graph.cypher.begin()
            for m in self.members:
                query = cypher.MEMBER_DELETE_QUERY.format(sf_id=m['sf_id'])
                tx.append(query)
                logger.debug("<Delete MEMBER>: {0}\n{1}\n".format(m['sf_id'], query))
            results = tx.commit()
        except:
            logger.exception("<Delete MEMBER>: error encountered.")
            return False, None
        else:
            if tx.finished:
                logger.info("<Delete MEMBER>: SYNC OK.")
                return True, results
            else:
                logger.error("<Delete MEMBER>: SYNC OK.")
                return False, None

    def test_add_memberships(self):
        try:
            tx = self.graph.cypher.begin()
            for sf_id, mship in self.memberships.items():
                query = cypher.MEMBERSHIP_MERGE_QUERY.format(
                    member_id=mship['member_id'], group_id=mship['group_id'],
                    mship_id=sf_id, status=mship['status'], start=mship['start'],
                    end=mship['end'])
                tx.append(query)
                logger.debug("<Add MEMBERSHIP>: {0} ({1} - {2})\n{3}\n".format(
                    sf_id, mship['start'], mship['end'], query))
            results = tx.commit()
        except:
            logger.exception("<Add MEMBERSHIP>: error encountered.")
            return False, None
        else:
            if tx.finished:
                logger.info("<Add MEMBERSHIP>: SYNC OK.")
                return True, results
            else:
                return False, None

    def test_add_connections(self):
        # Note: 3 Connection relationships will be created.
        try:
            tx = self.graph.cypher.begin()
            for sf_id, mship in self.memberships.items():
                query = cypher.CONNECTION_ADD_QUERY.format(
                    a_id=mship['member_id'], group_id=mship['group_id'],
                    mship_id=sf_id)
                tx.append(query)
                logger.debug("<Add CONNECTION>:\n{0}\n".format(query))
            results = tx.commit()
        except:
            logger.exception("<Add CONNECTION>: error encountered.")
            return False, None
        else:
            if tx.finished:
                logger.info("<Add CONNECTION>: SYNC OK.")
                return True, results
            else:
                logger.error("<Add CONNECTION>: transaction fail to commit.")
                return False, None

    def test_delete_memberships(self):
        try:
            tx = self.graph.cypher.begin()
            for sf_id, mship in self.memberships.items():
                query = cypher.MEMBERSHIP_DELETE_QUERY.format(sf_id=sf_id)
                tx.append(query)
                logger.debug("<Delete MEMBERSHIP>: {0} ({1} - {2})\n{3}\n".format(
                    sf_id, mship['start'], mship['end'], query))
            results = tx.commit()
        except:
            logger.exception("<Delete MEMBERSHIP>: error encountered.")
            return False, None
        else:
            if tx.finished:
                logger.info("<Delete MEMBERSHIP>: SYNC OK.")
                return True, results
            else:
                logger.error("<Delete MEMBERSHIP>: transaction fail to commit.")
                return False, None

    def test_delete_connections(self):
        try:
            tx = self.graph.cypher.begin()
            for sf_id, mship in self.memberships.items():
                query = cypher.CONNECTION_DELETE_QUERY.format(
                    m_id=mship['member_id'], group_id=mship['group_id'],
                    mship_id=sf_id)
                tx.append(query)
                logger.debug("<Delete CONNECTION>:\n{0}\n".format(query))
            results = tx.commit()
        except:
            logger.exception("<Delete CONNECTION>: error encountered.")
            return False, None
        else:
            if tx.finished:
                logger.info("<Delete CONNECTION>: SYNC OK.")
                return True, results
            else:
                logger.error("<Delete CONNECTION>: transaction fail to commit.")
                return False, None

    def test_update_memberships(self, is_connected=True):
        # overlap=True: updated values create 8 Connection relationships.
        # overlap=False: updated values create = Connection relationships.
        try:
            tx = self.graph.cypher.begin()
            updated_start = 1998
            updated_end = 2008
            mship_count = 1

            for sf_id, mship in self.memberships.items():
                if not is_connected:
                    updated_start = mship_count * 1000
                    updated_end = mship_count * 1005
                mship_count += 1

                query = cypher.MEMBERSHIP_MERGE_QUERY.format(
                    member_id=mship['member_id'], group_id=mship['group_id'],
                    mship_id=sf_id, status=mship['status'],
                    start=updated_start, end=updated_end)
                tx.append(query)
                logger.debug("<Update MEMBERSHIP>: {0} ({1} - {2})\n{3}\n".format(
                    sf_id, updated_start, updated_end, query))
            results = tx.commit()
        except:
            logger.exception("<Update MEMBERSHIP>: error encountered.")
            return False, None
        else:
            if tx.finished:
                logger.info("<Update MEMBERSHIP>: SYNC OK.")
                return True, results
            else:
                logger.error("<Update MEMBERSHIP>: transaction fail to commit.")
                return False, None

    def test_update_connections(self, is_connected=True):
        status, results = self._update_connection_dates(is_connected=is_connected)
        if status:
            status, results = self._delete_outdated_connections()
            if status:
                logger.info("<Update CONNECTION>: SYNC OK.")
                return status, results
        return False, None

    def _update_connection_dates(self, is_connected=True):
        try:
            tx = self.graph.cypher.begin()
            updated_start = 1998
            updated_end = 2008
            mship_count = 1

            for sf_id, mship in self.memberships.items():
                if not is_connected:
                    updated_start = mship_count * 1000
                    updated_end = mship_count * 1005
                mship_count += 1

                get_query = cypher.CONNECTION_GET_QUERY.format(
                    a_id=mship['member_id'], group_id=mship['group_id'],
                    mship_id=sf_id)
                connection_results = self.graph.cypher.execute(get_query)
                logger.debug("<Get CONNECTION>: {0} results.".format(
                    len(connection_results)))

                for connect_record in connection_results:
                    c_rel = connect_record[0].properties
                    node = self._get_related_node(c_rel, mship['member_id'])

                    if (updated_start == node['head_start']
                            and updated_end == node['head_end']):
                        # Do nothing if dates not changed.
                        continue
                    else:
                        # Dates have changed so update values.
                        query = cypher.CONNECTION_UPDATE_QUERY.format(
                            m_id=mship['member_id'],
                            group_id=mship['group_id'],
                            mship_label=node['mship_label'],
                            mship_id=sf_id,
                            id_label=node['id_label'],
                            start_label=node['start_label'],
                            end_label=node['end_label'],
                            m_start=updated_start,
                            m_end=updated_end)

                        logger.debug("<Update existing CONNECTION>:\n{0}\n".format(query))
                    tx.append(query)
                tx.process()

            results = tx.commit()
        except:
            logger.exception("<Update existing CONNECTION>: error encountered.")
            return False, None
        else:
            if tx.finished:
                logger.info("<Update existing CONNECTION>: OK.")
                return True, results
            else:
                logger.error("<Update existing CONNECTION>: transaction fail to commit.")
                return False, None

    def _delete_outdated_connections(self):
        try:
            tx = self.graph.cypher.begin()
            for sf_id, mship in self.memberships.items():
                get_query = cypher.CONNECTION_GET_QUERY.format(
                    a_id=mship['member_id'], group_id=mship['group_id'],
                    mship_id=sf_id)
                connection_results = self.graph.cypher.execute(get_query)
                logger.debug("<Get CONNECTION>: {0} results.".format(
                    len(connection_results)))

                for connect_record in connection_results:
                    c_rel = connect_record[0].properties

                    if (c_rel['_a_start'] > c_rel['_b_end'] or
                            c_rel['_b_start'] > c_rel['_a_end']):
                        # Dates no longer overlap so delete.
                        query = cypher.CONNECTION_DELETE_QUERY.format(
                            m_id=mship['member_id'], group_id=mship['group_id'],
                            mship_id=sf_id)
                        logger.debug(("<Delete CONNECTION>:\n{0}\n\n{1}\n").format(
                            query, c_rel))
                        tx.append(query)
                tx.process()

            results = tx.commit()
        except:
            logger.exception("<Delete outdated CONNECTION>: error encountered.")
            return False, None
        else:
            if tx.finished:
                logger.info("<Delete outdated CONNECTION>: OK.")
                return True, results
            else:
                logger.error("<Delete outdated CONNECTION>: transaction fail to commit.")
                return False, None

    def _get_related_node(self, connect_rel, member_id):
        related_nodes = {
            # Member node 'A'
            connect_rel['_a_id']: {
                'head_start': connect_rel['_a_start'],
                'head_end': connect_rel['_a_end'],
                'tail_start': connect_rel['_b_start'],
                'tail_end': connect_rel['_b_end'],
                'mship_label': '_a_mship',
                'id_label': '_a_id',
                'start_label': '_a_start',
                'end_label': '_a_end'
            },
            # Member node 'B'
            connect_rel['_b_id']: {
                'head_start': connect_rel['_b_start'],
                'head_end': connect_rel['_b_end'],
                'tail_start': connect_rel['_a_start'],
                'tail_end': connect_rel['_a_end'],
                'mship_label': '_b_mship',
                'id_label': '_b_id',
                'start_label': '_b_start',
                'end_label': '_b_end'
            }
        }

        return related_nodes.get(member_id, None)
