from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import utc
from optparse import make_option
from py2neo import cypher
import datetime
import time

from taikonetwork.neo4j_settings import NEO4J_ROOT_URI
from datahandler.models import Group, Member, Membership, SyncInfo


class Command(BaseCommand):
    help = "Checks if the Neo4j database is synchronized with the \
    SalesForce database. Displays the count of newly-added or \
    recently-modified objects. No updates are executed on the databases. \
    To update, use option '--sync'."

    option_list = BaseCommand.option_list + (
        make_option('--sync',
                    action='store_true',
                    dest='sync',
                    default=False,
                    help="Synchronizes the Neo4j database with newly-added \
                    and recently-modified data from the SalesForce database. \
                    All database updates (transactions) are logged to [dir]'."),
    )

    def handle(self, **options):
        self.stdout.write('> Checking SalesForce database for updates...')

        try:
            groupinfo = SyncInfo.objects.get(model_type='Group')
            memberinfo = SyncInfo.objects.get(model_type='Member')
            membershipinfo = SyncInfo.objects.get(model_type='Membership')
        except SyncInfo.DoesNotExist:
            self.stderr.write('SyncInfo does not exist.')

        if options['sync']:
            start = time.time()

            try:
                # Query newly-added or recently-modified data
                # (lastmodifieddate >= lastupdateddate)
                groups, members, mships = query_updated_data(groupinfo.lastupdateddate,
                            memberinfo.lastupdateddate, membershipinfo.lastupdateddate)

                num_groups = len(groups)
                num_members = len(members)
                num_mships = len(mships)
                self.stdout.write("> 'Group' update count: {}".format(num_groups))
                self.stdout.write("> 'Member' update count: {}".format(num_members))
                self.stdout.write("> 'Membership' update count: {}".format(num_mships))

                self.stdout.write('> Syncing SalesForce and NEO4J databases...')
                # Connect session using root service uri for Cypher transactions.
                self.session = cypher.Session(NEO4J_ROOT_URI)

                # Update nodes and relationships.
                # Set SyncInfo to latest date on proper sync.
                if num_groups > 0:
                    group_sync_ok = self._update_node_groups(groups)
                    if group_sync_ok:
                        groupinfo.save()

                if num_members > 0:
                    member_sync_ok = self._update_node_members(members)
                    if member_sync_ok:
                        memberinfo.save()

                # Membership and Connection relationships dependent on nodes.
                # Sync relationships only if Group and Member nodes updated error-free. 
                rel_error = True
                if group_sync_ok and member_sync_ok and num_mships > 0:
                    # Format Membership queryset to dictionary for easier updating
                    # and for reducing SalesForce API calls.
                    self._format_membership_data(mships)
                    rel_error = self._batch_update_relationships()

                if not rel_error:
                    end = time.time()
                    self.stdout.write('[STATUS] Databases are now synchronized.\n')
                    self.stdout.write('Elapsed Time: %M minutes %S seconds.',
                                      time.gmtime(end-start))
                else:
                    self.stderr.write('[STATUS] Error encountered during sync. \n'
                                      '> Please check logs and databases '
                                      'and try again.')
            except:
                self.stderr.write('! --- UNEXPECTED ERROR ENCOUNTERED --- !\n')
                self.stderr.write(sys.exc_info()[0])
                raise
        else:
            num_groups = Group.objects.filter(accounttype='Taiko Group',
                                lastmodifieddate__lt=group_updatedate).count()
            num_members = Member.objects.filter(
                           lastmodifieddate__lt=member_lastupdatedate).count()
            num_mships = Membership.objects.filter(
                           lastmodifieddate__lt=membership_updatedate).count()

            self.stdout.write("> 'Group' update count: {}".format(num_groups))
            self.stdout.write("> 'Member' update count: {}".format(num_members))
            self.stdout.write("> 'Membership' update count: {}".format(num_mships))

            self.stdout.write(">>> To execute these updates and synchronize "
                              "the NEO4J database with the SalesForce database, "
                              "re-run commans with '--sync' option.")


    def query_updated_data(group_updatedate, member_updatedate,
                               membership_updatedate):
        groups = Group.objects.filter(accounttype='Taiko Group',
                      lastmodifieddate__lt=group_updatedate).values(
                          'Id', 'name', 'is_deleted')

        members = Member.objects.filter(
                       lastmodifieddate__lt=member_lastupdatedate).values(
                           'Id', 'firstname', 'lastname', 'dob', 'gender',
                           'race', 'asian_ethnicity', 'is_deleted')

        mships = Membership.objects.filter(
                           lastmodifieddate__lt=membership_updatedate).values(
                               'Id', 'member', 'group', 'status',
                               'startdate', 'enddate', 'is_deleted')

        return groups, members, mships


    def _format_membership_data(mships)
        self.group_memberships = {}
        for s in mships:
            # Rules for dealing with incomplete date information.
            if s.startdate == None and s.enddate == None:
                if s.status == 'Current':
                    startyear = 9999
                    endyear = 9999
                else:
                    startyear = 'null'
                    endyear = 'null'
            elif s.startdate != None and s.enddate == None:
                if s.status == 'Current':
                    startyear = s.startdate.year
                    endyear = 9999
                else:
                    startyear = s.startdate.year
                    endyear = s.startdate.year
            elif s.startdate == None and s.enddate != None:
                startyear = s.enddate.year
                endyear = s.enddate.year
            elif s.startdate != None and s.enddate != None:
                startyear = s.startdate.year
                endyear = s.enddate.year

            membership_dict = {'member_id': s.member_id,
                               'group_id': s.group_id,
                               'status': s.status,
                               'start': startyear,
                               'end': endyear,
                               'is_deleted': s.is_deleted}

            added = self.group_memberships.get(s.group_id, None)
            if added:
                self.group_memberships[s.group_id][s.Id] = membership_dict
            else:
                self.group_memberships[s.group_id] = {s.Id: membership_dict}


    def _batch_update_relationships(self):
        count = 0
        batch = 1
        rel_error = False
        self.stdout.write("--- BATCH #{} ---".format(batch))
        self.session = cypher.Session(NEO4J_ROOT_URI)

        for group, memberships in self.group_memberships.items():
            count += 1;
            if count >= 38:
                count = 0
                batch += 1
                # Re-connect session for each batch
                self.session = cypher.Session(NEO4J_ROOT_URI)
                self.stdout.write("--- BATCH #{} ---".format(batch))

            memship_sync_ok, num_memship = self._update_rel_memberships(memberships)
            connect_sync_ok, num_connect = self._update_rel_connections(memberships)

            if not memship_sync_ok and connect_sync_ok:
                rel_error = True
                self.stderr.write('! GROUP: ["{0}"] -- Error syncing Memberships/Connections.')
            else:
                connect_count = nCr(num_connect, 2)
                self.stdout.write('- GROUP: ["{0}"] -- # Membership: {1}, '
                                  '# Connection: {2}'.format(group,
                                                             num_memship,
                                                             connect_count))
        return rel_error


    ####################################################
    # Methods for syncing NEO4J nodes and relationships
    #     via Cypher transactions.
    ####################################################
    def _update_node_groups(self, groups):
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
                    self.stdout.write("> REMOVED 'Group' node: {0}".format(
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
            self.stderr.write('! --- TRANSACTION ERROR --- !\n')
            self.stderr.write(str(error))

            return False
        else:
            if tx.finished:
                self.stdout.write(">>> [{0}] 'Group' node(s) successfully "
                                  "synced.".format(num_group_nodes))
                if num_removed:
                    self.stdout.write(">>> [{0}] 'Group' node(s) removed.".format(
                        num_removed))

                return True
            else:
                return False


    def _update_node_members(self, members):
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
            num_member_nodes = tx.commit()
        except cypher.TransactionError as error:
            self.stderr.write('! --- TRANSACTION ERROR --- !\n')
            self.stderr.write(str(error))

            return False
        else:
            if tx.finished:
                self.stdout.write(">>> [{0}] 'Member' node(s) successfully "
                                  "synced.".format(num_member_nodes))
                if num_removed:
                    self.stdout.write(">>> [{0}] 'Member' node(s) "
                                      "removed.".format(num_removed))

                return True
            else:
                return False


    def _update_rel_memberships(self, memberships):
        merge_cypher = ('MATCH (m_node:Member {{ sf_id: "{member_id}" }}),'
                        '(g_node:Group {{ sf_id: "{group_id}" }}) '
                        'MERGE (m_node)-[rel:MEMBER_OF]->(g_node) '
                        'ON CREATE SET rel += {{ '
                        'sf_id: "{rel_id}", '
                        'status: "{status}", '
                        'start: toInt({start}), '
                        'end: toInt({end}), '
                        '_is_new: true }} '
                        'ON MATCH SET rel += {{ '
                        'status: "{status}", '
                        'start: toInt({start}), '
                        'end: toInt({end}), '
                        '_is_new: false, '
                        '_count: coalesce(_count?, 0) + 1 }} '
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
                    self.stdout.write('! MEMBERSHIP_IS_DELETED: {0}'.format(key))
                    #num_removed += 1
                    #query = delete_cypher.format(sf_id=d['Id'])
                else:
                    # Update or create if none exists.
                    query = merge_cypher.format(member_id=d['member_id'],
                                                group_id=d['group_id'],
                                                rel_id=d['Id'],
                                                status=d['status'],
                                                start=d['start'],
                                                end=d['end'])
                tx.append(query)

            # Execute all queries on server and commit transaction.
            # Save results.
            self.membership_rels = tx.commit()
        except cypher.TransactionError as error:
            self.stderr.write('! --- TRANSACTION ERROR --- !\n')
            self.stderr.write(str(error))

            return False
        else:
            if tx.finished:
                num_results = len(self.membership_rels)
                # Nested empty lists returned when no query matches or updates.
                if num_results == 1:
                    num_results = len(self.membership_rels[0])

                if num_removed:
                    self.stdout.write(">>> [{0}] 'Membership' relationship(s) "
                                      "removed.".format(num_removed))
                return True, num_results
            else:
                return False


    def _update_rel_connections(self, memberships):
        ret_cypher = ('MATCH (a:Member {{sf_id: "{a_id}" }})-[c:CONNECTED_TO '
                      '{{group_id: "{group_id}" }}]-(b:Member) RETURN c')

        new_cypher = ('MATCH (a:Member '
                      '{{sf_id: "{a_id}" }})-[r1:MEMBER_OF]->(g:Group '
                      '{{sf_id: "{g_id}"}}), '
                      '(b:Member)-[r2:MEMBER_OF]->(g:Group '
                      '{{sf_id: "{g_id}"}}) '
                      'WHERE NOT a = b AND r1.start <= r2.end '
                      'AND r2.start <= r1.end '
                      'MERGE (a)-[c:CONNECTED_TO {{group_id:g.sf_id}}]-(b) '
                      'ON CREATE SET c += {{ '
                      'group: g.name, '
                      '_a_id: a.sf_id, '
                      '_a_start: r1.start, '
                      '_a_end: r1.end, '
                      '_b_id: b.sf_id, '
                      '_b_start: r2.start, '
                      '_b_end: r2.end }} '
                      'RETURN c')

        update_cypher = ('MATCH (a:Member {{sf_id: "{a_id}" }})-'
                         '[c:CONNECTED_TO {{group_id: "{group_id}" }}]-(b:Member) '
                         'SET c += {{ '
                         '{m_name}: "{a_id}", '
                         '{m_start}: {start}, '
                         '{m_end}: {end} }}')

        delete_cypher = ('MATCH (a:Member {{sf_id: "{a_id}" }})-'
                         '[c:CONNECTED_TO {{group_id: "{group_id}" }}]-(b:Member) '
                         'DELETE c')

        try:
            tx = self.session.create_transaction()
            num_removed = 0

            # Check which memberships were deleted, then
            # remove all related connections.
            for key, d in memberships:
                if d['is_deleted']:
                    num_removed += 1
                    query = delete_cypher.format(a_id=d['member_id'],
                                                 group_id=d['group_id'])
                    tx.append(query)

            # Iterate through newly-created/updated memberships and
            # update its corresponding connections.
            for membership_rel in self.membership_rels:
                # Get properties dict from membership Relationship object.
                # This is a HACK for working with Record results from
                # cypher transactions. Due to wrong uri (localhost instead
                # of remote), connection is refused (unresolved bug in py2neo?).
                rel = membership_rel[0][0]._properties

                d = memberships[rel['sf_id']]
                if rel['_is_new']:
                    # If newly-added membership relationship,
                    # create new connection relationships.
                    query = new_cypher.format(a_id=d['member_id'],
                                              g_id=d['group_id'])
                    tx.append(query)
                else:
                    # If modified and existing membership relationship,
                    # update/delete connection relationships.
                    # Get all connections related to specified membership.
                    ret_query = ret_cypher.format(a_id=d['member_id'],
                                                  group_id=d['group_id'])
                    connections = self.session.execute(ret_query)

                    # For each connection relation, check if updated startyear
                    # endyear still overlap.
                    for connect in connections:
                        # HACK (see above): get properties dict from
                        # connection Relationship object.
                        c = connect[0]._properties

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
                                    query = update_cypher.format(m_name="_a_id",
                                                        a_id = d['member_id'],
                                                        group_id=d['group_id'],
                                                        m_start="_a_start",
                                                        m_end="_a_end",
                                                        start=rel['start'],
                                                        end=rel['end'])
                                else:
                                    # Dates no longer overlap, so remove.
                                    query = delete_cypher.format(
                                                         a_id=d['member_id'],
                                                         group_id=d['group_id'])

                        elif d['member_id'] == c['_b_id']:
                            if rel['start'] == c['_b_start'] and \
                               rel['end'] == c['_b_end']:
                                continue
                            else:
                                if rel['start'] <= c['_a_end'] and \
                                   c['_a_start'] <= rel['end']:
                                    query = update_cypher.format(m_name="_b_id",
                                                        a_id=d['member_id'],
                                                        group_id=d['group_id'],
                                                        m_start="_b_start",
                                                        m_end="_b_end",
                                                        start=rel['start'],
                                                        end=rel['end'])
                                else:
                                    query = delete_cypher.format(
                                                         a_id=d['member_id'],
                                                         group_id=d['group_id'])

                        tx.append(query)

            connection_rels = tx.commit()
        except cypher.TransactionError as error:
            self.stderr.write('! --- TRANSACTION ERROR --- !\n')
            self.stderr.write(str(error))

            return False
        else:
            if tx.finished:
                num_results = len(connection_rels)
                # Nested empty lists returned when no query matches or updates.
                if num_results == 1:
                    num_results = len(connection_rels[0])

                self.stdout.write(">>> [{0}] 'Connection' relationship(s) "
                                  "successfully synced.".format(num_results))
                if num_removed:
                    self.stdout.write(">>> [{0}] 'Connection' relationship(s) "
                                      "removed.".format(num_removed))

                return True, num_results
            else:
                return False
