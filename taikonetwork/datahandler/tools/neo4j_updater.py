"""
    datahandler.tools.neo4j_updater
    --------------------------------


"""
import logging
from datetime import datetime

from datahandler.models import Group, Member, Membership, Neo4jSyncInfo
from py2neo import cypher
from taikonetwork.neo4j_settings import NEO4J_ROOT_URI


# Get instance of logger for Neo4jUpdater.
logger = logging.getLogger('datahandler.neo4j_updater')


class Neo4jUpdater():
    def __init__(self):
        """Get latest sync information and Neo4j database connection."""
        try:
            self.groupinfo = Neo4jSyncInfo.objects.get(model_type='Group')
            self.memberinfo = Neo4jSyncInfo.objects.get(model_type='Member')
            self.mshipinfo = Neo4jSyncInfo.objects.get(model_type='Membership')
        except Neo4jSyncInfo.DoesNotExist as error:
            logger.error('Neo4jSyncInfo object does no exist.')
            raise Exception(error)

        self.session = cypher.Session(NEO4J_ROOT_URI)

    def check_sql_db(self):
        num_groups = Group.objects.filter(
            lastmodifieddate__lt=self.groupinfo.lastupdateddate).count()
        num_members = Member.objects.filter(
            lastmodifieddate__lt=self.memberinfo.lastupdateddate).count()
        num_mships = Membership.objects.filter(
            lastmodifieddate__lt=self.mshipinfo.lastupdateddate).count()

        return num_groups, num_members, num_mships

    def update_group_nodes(self):
        delete_query = ('MATCH (node:Group {{ sf_id: "{sf_id}" }})-[rel]-() '
                        'DELETE node, rel')
        merge_query = ('MERGE (node:Group {{ sf_id: "{0}" }}) '
                       'ON CREATE SET node.name = "{1}" RETURN count(node)')
        merge_fields = ['sf_id', 'name']

        try:
            groups = Group.objects.filter(
                lastmodifieddate__lt=self.groupinfo.lastupdateddate)
            sync_ok = self._execute_cypher_queries("'Group' node", groups,
                                                   delete_query, merge_query,
                                                   merge_fields)
            return sync_ok
        except Group.DoesNotExist:
            logger.error("'Group' object does not exist.")
            return False

    def update_member_nodes(self):
        delete_query = ('MATCH (node:Member {{ sf_id: "{sf_id}" }})-[rel]-() '
                        'DELETE node, rel')
        merge_query = ('MERGE (node:Member {{ sf_id: "{0}" }}) '
                       'ON CREATE SET node += {{ '
                       'firstname: "{1}", '
                       'lastname: "{2}", '
                       'dob: "{3}", '
                       'gender: "{4}", '
                       'race: "{5}", '
                       'asian_ethnicity: "{6}" }}'
                       'ON MATCH SET node += {{ '
                       'firstname: "{7}", '
                       'lastname: "{8}", '
                       'dob: "{9}", '
                       'gender: "{10}", '
                       'race: "{11}", '
                       'asian_ethnicity: "{12}" }} '
                       'RETURN count(node)')
        merge_fields = ['sf_id', 'firstname', 'lastname', 'dob', 'gender',
                        'race', 'asian_ethnicity', 'firstname', 'lastname',
                        'dob', 'gender', 'race', 'asian_ethnicity']

        try:
            members = Member.objects.filter(
                lastmodifieddate__lt=self.memberinfo.lastupdateddate)
            sync_ok = self._execute_cypher_queries("'Member' node", members,
                                                   delete_query, merge_query,
                                                   merge_fields)
            return sync_ok
        except Member.DoesNotExist:
            logger.error("'Member' object does not exist.")
            return False

    def _execute_cypher_queries(self, model_type, objects, delete_query,
                                merge_query, merge_fields):
        try:
            tx = self.session.create_transaction()
            num_removed = 0

            for obj in objects:
                if obj.is_deleted:
                    logger.debug("Removed {0}: {1}".format(model_type, obj.name))
                    num_removed += 1
                    query = delete_query.format(sf_id=obj.sf_id)
                else:
                    # Update existing or create if none exists.
                    values = [str(getattr(obj, field)) for field in merge_fields]
                    query = merge_query.format(*values)
                tx.append(query)

            # Execute all queries and commit transaction.
            results = tx.commit()
        except cypher.TransactionError as neo4j_error:
            logger.error("Neo4j: {0}".format(neo4j_error))
            return False
        else:
            if tx.finished:
                num_results = len(results)
                # Nested empty lists returned when no query matches or updates.
                if num_results == 1:
                    num_results = len(results[0])
                status_msg = ("> ({0}) {1}(s) synced.".format(
                    num_results, model_type))
                if num_removed:
                    status_msg += (" ({0}) {1}(s) removed.".format(
                        num_removed, model_type))

                logger.info(status_msg)
                return True
            else:
                logger.error("Neo4j: Transaction for {0}(s) failed to commit.")
                return False

    def batch_update_relationships(self):
        group_mships_dict = self._get_and_format_memberships()

        for group, memberships in group_mships_dict.items():
            mship_sync_ok, mship_sync_count, mship_remove_count = \
                self._update_membership_rels(memberships)

            if mship_sync_ok and (mship_sync_count or mship_remove_count):
                conn_sync_ok, conn_sync_count, conn_remove_count = \
                    self._update_connection_rels(memberships)

                if conn_sync_ok and (conn_sync_count and conn_remove_count):
                    logger.debug(("> [{0}] Memberships: ({1}) synced, "
                                  "({2}) removed.".format(group, mship_sync_count,
                                                          mship_remove_count)))

    def _get_and_format_memberships(self):
        """Format list of Membership objects as a dictionary of dictionaries
           keyed by the related group's 'sf_id', and apply rules for dealing
           with incomplete date information. Allows for batch updating
           relationships (Memberships and Connections).

        """
        try:
            memberships = Membership.objects.filter(
                lastmodifieddate__lt=self.mshipinfo.lastupdateddate)
        except Membership.DoesNotExist:
            logger.error("'Membership' object does not exist.")
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
            added = group_mships_dict.get(s.group_id, None)
            if added:
                group_mships_dict[s.group_id][s.sf_id] = membership_dict
            else:
                group_mships_dict[s.group_id] = {s.sf_id: membership_dict}

        return group_mships_dict

    def _update_membership_rels(self, memberships):
        delete_query = ('MATCH (m:Member)-[rel:MEMBER_OF]->(g:Group) '
                        'WHERE rel.sf_id = "{sf_id}" DELETE rel')
        merge_query = ('MATCH (m_node:Member {{ sf_id: "{member_id}" }}),'
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

        try:
            tx = self.session.create_transaction()
            num_removed = 0

            for sf_id, mship in memberships.items():
                if mship['is_deleted']:
                    logger.debug("Removed 'Membership' rel: {0}".format(sf_id))
                    num_removed += 1
                    query = delete_query.format(sf_id=sf_id)
                else:
                    # Update existing or create if none exists.
                    query = merge_query.format(member_id=mship['member_id'],
                                               group_id=mship['group_id'],
                                               mship_id=sf_id,
                                               status=mship['status'],
                                               start=mship['start'],
                                               end=mship['end'])
                tx.append(query)

            # Execute all queries and commit transaction. Save results.
            self.membership_rels = tx.commit()
        except cypher.TransactionError as neo4j_error:
            logger.error("Neo4j: {0}".format(neo4j_error))
            return (False, 0, 0)
        else:
            if tx.finished:
                num_results = len(self.membership_rels)
                # Nested empty lists returned when no query matches or updates.
                if num_results == 1:
                    num_results = len(self.membership_rels[0])

                return (True, num_results, num_removed)
            else:
                logger.error("Neo4j: Transaction for 'Membership' "
                             "relationship(s) failed to commit.")
                return (False, 0, 0)

    def _update_connection_rels(self):
        return False
