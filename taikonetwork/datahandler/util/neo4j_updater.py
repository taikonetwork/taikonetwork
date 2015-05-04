"""
    datahandler.util.neo4j_updater
    --------------------------------


"""
import logging
from datetime import datetime

from datahandler.models import Group, Member, Membership, Neo4jSyncInfo
from py2neo import authenticate, Graph, GraphError
from taikonetwork.authentication import Neo4jAuth as neo4j
from datahandler.util import neo4j_cypher as cypher


# Get instance of logger for Neo4jUpdater.
logger = logging.getLogger('datahandler.neo4j_updater')


class Neo4jUpdater:
    def __init__(self):
        """Get latest sync information and Neo4j database connection."""
        try:
            self.groupinfo = Neo4jSyncInfo.objects.get(model_type='Group')
            self.memberinfo = Neo4jSyncInfo.objects.get(model_type='Member')
            self.mshipinfo = Neo4jSyncInfo.objects.get(model_type='Membership')
        except Neo4jSyncInfo.DoesNotExist as error:
            logger.error('Neo4jSyncInfo object does no exist.')
            raise Exception(error)

        authenticate(neo4j.HOST_PORT, neo4j.USERNAME, neo4j.PASSWORD)
        self.graph = Graph(neo4j.REMOTE_URI)

    def check_sql_db(self):
        num_groups = Group.objects.filter(
            lastmodifieddate__gt=self.groupinfo.lastupdateddate).count()
        num_members = Member.objects.filter(
            lastmodifieddate__gt=self.memberinfo.lastupdateddate).count()
        num_mships = Membership.objects.filter(
            lastmodifieddate__gt=self.mshipinfo.lastupdateddate).count()

        return num_groups, num_members, num_mships

    def update_group_nodes(self):
        try:
            groups = Group.objects.filter(
                lastmodifieddate__gt=self.groupinfo.lastupdateddate)
            merge_fields = ['sf_id', 'name']
            sync_ok = self._execute_node_queries("<Group>", groups,
                                                 cypher.GROUP_DELETE_QUERY,
                                                 cypher.GROUP_MERGE_QUERY,
                                                 merge_fields)
            if sync_ok:
                self.groupinfo.save()
            return sync_ok
        except:
            logger.exception("Group: unexpected error encountered.")
            return False

    def update_member_nodes(self):
        try:
            members = Member.objects.filter(
                lastmodifieddate__gt=self.memberinfo.lastupdateddate)
            merge_fields = ['sf_id', 'firstname', 'lastname', 'dob', 'gender',
                            'race', 'asian_ethnicity']
            sync_ok = self._execute_node_queries("<Member>", members,
                                                 cypher.MEMBER_DELETE_QUERY,
                                                 cypher.MEMBER_MERGE_QUERY,
                                                 merge_fields)
            if sync_ok:
                self.memberinfo.save()
            return sync_ok
        except:
            logger.exception("Member: unexpected error encountered.")
            return False

    def _execute_node_queries(self, model_type, objects, delete_query,
                              merge_query, merge_fields):
        try:
            tx = self.graph.cypher.begin()

            for obj in objects:
                if obj.is_deleted:
                    logger.debug("Removed {0} node: {1}".format(model_type, obj.name))
                    query = delete_query.format(sf_id=obj.sf_id)
                else:
                    # Update existing or create if none exists.
                    values = [str(getattr(obj, field)) for field in merge_fields]
                    query = merge_query.format(*values)
                tx.append(query)

            # Execute all queries and commit transaction.
            results = tx.commit()
        except GraphError:
            logger.exception("Neo4j: error during {0} sync.".format(model_type))
            return False
        else:
            if tx.finished:
                num_synced = 0
                for r in results:
                    num_synced += r[0][0]

                logger.info("> ({0}) {1} node(s) synced.".format(
                    num_synced, model_type))
                return True
            else:
                logger.error("Neo4j: {0} transaction failed to commit.".format(
                    model_type))
                return False

    def batch_update_relationships(self):
        group_mships_dict = self._get_and_format_memberships()

        total_mship_synced = 0
        total_conn_synced = 0
        rel_sync_ok = True
        for group, memberships in group_mships_dict.items():
            (mship_sync_ok, num_mship_synced, has_deletions) = \
                self._update_membership_rels(memberships)

            if mship_sync_ok and num_mship_synced > 0:
                total_mship_synced += num_mship_synced
                logger.debug(("- [{0}] Membership: ({1}) synced.".format(
                              group[1], num_mship_synced)))

                (conn_sync_ok, num_conn_synced, status_msg) = \
                    self._update_connection_rels(memberships, has_deletions)
                total_conn_synced += num_conn_synced
                logger.debug("- [{0}] {1}".format(group[1], status_msg))

                if not conn_sync_ok:
                    rel_sync_ok = False
            elif not mship_sync_ok:
                rel_sync_ok = False

        logger.info("> ({0}) <Membership> relationship(s) synced.".format(total_mship_synced))
        logger.info("> ({0}) <Connection> relationship(s) synced.".format(total_conn_synced))
        if rel_sync_ok:
            self.mshipinfo.save()
        return rel_sync_ok

    def _get_and_format_memberships(self):
        """Format list of Membership objects as a dictionary of dictionaries
           keyed by the related group's 'sf_id', and apply rules for dealing
           with incomplete date information. Allows for batch updating
           relationships (Memberships and Connections).

        """
        try:
            memberships = Membership.objects.filter(
                lastmodifieddate__gt=self.mshipinfo.lastupdateddate)
        except:
            logger.exception("Membership: unexpected error encountered.")
            return {}

        group_mships_dict = {}
        for s in memberships:
            if s.startdate is not None and s.enddate is not None:
                startyear = s.startdate.year
                endyear = s.enddate.year
            # No start date: set start to end year.
            elif s.startdate is None and s.enddate is not None:
                startyear = s.enddate.year
                endyear = s.enddate.year
            # No end date: if 'Current' status, set end to indefinite (9999).
            # Otherwise, set end to start year.
            elif s.startdate is not None and s.enddate is None:
                if s.status == 'Current':
                    startyear = s.startdate.year
                    endyear = 9999
                else:
                    startyear = s.startdate.year
                    endyear = s.startdate.year
            # No data provided: if 'Current' status, set start to this year and
            # end to indefinite (9999). Otherwise, set both to NULL.
            elif s.startdate is None and s.enddate is None:
                if s.status == 'Current':
                    startyear = datetime.now().year
                    endyear = 9999
                else:
                    startyear = 'null'
                    endyear = 'null'

            membership_dict = {'member_id': s.member.sf_id,
                               'group_id': s.group.sf_id,
                               'status': s.status,
                               'start': startyear,
                               'end': endyear,
                               'is_deleted': s.is_deleted}
            group_tuple_key = (s.group.sf_id, s.group.name)
            added = group_mships_dict.get(group_tuple_key, None)
            if added:
                group_mships_dict[group_tuple_key][s.sf_id] = membership_dict
            else:
                group_mships_dict[group_tuple_key] = {s.sf_id: membership_dict}

        return group_mships_dict

    def _update_membership_rels(self, memberships):
        try:
            tx = self.graph.cypher.begin()
            has_deletions = False

            for sf_id, mship in memberships.items():
                if mship['is_deleted']:
                    has_deletions = True
                    logger.debug("Removed <Membership> rel: {0}".format(sf_id))
                    query = cypher.MEMBERSHIP_DELETE_QUERY.format(sf_id=sf_id)
                else:
                    # Update existing or create if none exists.
                    query = cypher.MEMBERSHIP_MERGE_QUERY.format(
                        member_id=mship['member_id'], group_id=mship['group_id'],
                        mship_id=sf_id, status=mship['status'],
                        start=mship['start'], end=mship['end'])
                tx.append(query)

            # Execute all queries and commit transaction. Save results.
            results = tx.commit()
        except GraphError:
            logger.exception("Neo4j: error during <Membership> sync.")
            return (False, 0, False)
        else:
            if tx.finished:
                num_synced = 0
                for r in results:
                    num_synced += r[0][0]
                return (True, num_synced, has_deletions)
            else:
                logger.error("Neo4j: <Membership> transaction failed to commit.")
                return (False, 0, False)

    def _update_connection_rels(self, memberships, has_deletions):
        try:
            delete_ok, num_deleted = True, 0
            if has_deletions:
                delete_ok, num_deleted = self._remove_deleted_connections(memberships)
            update_ok, num_updated = self._update_existing_connections(memberships)
            outdated_ok, num_outdated = self._remove_outdated_connections(memberships)
            add_ok, num_added = self._add_new_connections(memberships)
        except GraphError:
            logger.exception("Neo4j: error encountered during transaction.")
            return (False, 0, None)
        else:
            if delete_ok and update_ok and outdated_ok and add_ok:
                status_msg = ("Connection: ({0}) added, ({1}) updated, ({2}) "
                              "removed.".format(num_added, num_updated,
                                                num_deleted + num_outdated))
                num_synced = int((num_added + num_updated + num_deleted
                                  + num_outdated) / 2)
                return (True, num_synced, status_msg)
            else:
                status_msg = ("Connection: sync failed.")
                return (False, 0, status_msg)

    def _remove_deleted_connections(self, memberships):
        """Remvoe Connection rels associated with deleted Membership rels."""
        tx = self.graph.cypher.begin()

        for sf_id, mship in memberships.items():
            if mship['is_deleted']:
                logger.debug("Removed <Connection> rel(s) associated with "
                             "Membership:{0}".format(sf_id))
                query = cypher.CONNECTION_DELETE_QUERY.format(
                    m_id=mship['member_id'], group_id=mship['group_id'],
                    mship_id=sf_id)
                tx.append(query)

        results = tx.commit()
        if tx.finished:
            num_deleted = 0
            for r in results:
                num_deleted += r[0][0]
            return True, num_deleted
        else:
            return False, None

    def _update_existing_connections(self, memberships):
        """Update existing Connection relationships associated with
            recently-modified Membership(s).

        """
        tx = self.graph.cypher.begin()

        for sf_id, mship in memberships.items():
            if not mship['is_deleted']:
                # Get all Connections associated to specified Membership
                get_query = cypher.CONNECTION_GET_QUERY.format(
                    a_id=mship['member_id'], group_id=mship['group_id'],
                    mship_id=sf_id)
                connection_results = self.graph.cypher.execute(get_query)

                for connect_record in connection_results:
                    # type(connect_record) = Record
                    # type(connect_record[0]) = Relationship
                    c_rel = connect_record[0].properties
                    node = self._get_related_node(c_rel, mship['member_id'])

                    if (mship['start'] == node['head_start']
                            and mship['end'] == node['head_end']):
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
                            m_start=mship['start'],
                            m_end=mship['end'])
                        tx.append(query)
                tx.process()

        results = tx.commit()
        if tx.finished:
            num_updated = 0
            for r in results:
                num_updated += r[0][0]
            return True, num_updated
        else:
            return False, None

    def _remove_outdated_connections(self, memberships):
        tx = self.graph.cypher.begin()

        for sf_id, mship in memberships.items():
            if not mship['is_deleted']:
                # Get all Connections associated to specified Membership
                get_query = cypher.CONNECTION_GET_QUERY.format(
                    a_id=mship['member_id'], group_id=mship['group_id'],
                    mship_id=sf_id)
                connection_results = self.graph.cypher.execute(get_query)

                for connect_record in connection_results:
                    # type(connect_record) = Record
                    # type(connect_record[0]) = Relationship
                    c_rel = connect_record[0].properties

                    if (c_rel['_a_start'] > c_rel['_b_end'] or
                            c_rel['_b_start'] > c_rel['_a_end']):
                        # Dates no longer overlap so delete.
                        query = cypher.CONNECTION_DELETE_QUERY.format(
                            m_id=mship['member_id'], group_id=mship['group_id'],
                            mship_id=sf_id)
                        tx.append(query)
                tx.process()

        results = tx.commit()
        if tx.finished:
            num_outdated = 0
            for r in results:
                num_outdated += r[0][0]
            return True, num_outdated
        else:
            return False, None

    def _add_new_connections(self, memberships):
        """Add new Connection relationships for newly-created and
            recently-modified Membership relationships.

        """
        tx = self.graph.cypher.begin()

        for sf_id, mship in memberships.items():
            if not mship['is_deleted']:
                query = cypher.CONNECTION_ADD_QUERY.format(
                    a_id=mship['member_id'], group_id=mship['group_id'],
                    mship_id=sf_id)
                tx.append(query)

        results = tx.commit()
        if tx.finished:
            num_add = 0
            for r in results:
                num_add += r[0][0]
            return True, num_add
        else:
            return False, None

    def _get_related_node(self, connect_rel, member_id):
        """Determine the corresponding Member node (head or tail of relationship?)
            since Connection relationship is undirected and relationship
            labels are assigned arbitrarily.
        """
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
