from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import utc
from optparse import make_option
from py2neo import cypher
import datetime

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

        # Query newly-added or recently-modified data
        # (lastmodifieddate >= lastupdateddate)
        groups = Group.objects.filter(accounttype='Taiko Group',
            lastmodifieddate__lt=groupinfo.lastupdateddate)
        members = Member.objects.filter(
            lastmodifieddate__gte=memberinfo.lastupdateddate)
        memberships = Membership.objects.filter(
                    lastmodifieddate__lt=membershipinfo.lastupdateddate)

        #stanford = Group.objects.get(name='Stanford Taiko')
        #jun = Group.objects.get(name='Jun Daiko')
        #groups = [stanford, jun]

        #linda = Member.objects.get(name='Linda Uyechi')
        #susan = Member.objects.get(name='Susan Yuen')
        #members = [linda, susan]

        #linda_stanford = Membership.objects.get(member=linda, group=stanford)
        #linda_jun = Membership.objects.get(member=linda, group=jun)
        #susan_stanford = Membership.objects.get(member=susan, group=stanford)
        #susan_jun = Membership.objects.get(member=susan, group=jun)
        #memberships = [linda_stanford, linda_jun, susan_stanford, susan_jun]

        self.stdout.write("> Number of 'Group' updates: {}".format(len(groups)))
        self.stdout.write("> Number of 'Member' updates: {}".format(len(members)))
        self.stdout.write("> Number of 'Membership' updates: {}".format(len(memberships)))

        if options['sync']:
            self.stdout.write('> Syncing SalesForce and NEO4J databases...')
            # Connect session using root service uri for Cypher transactions.
            self.session = cypher.Session(NEO4J_ROOT_URI)

            # Update nodes and relationships.
            # Set SyncInfo to latest sync date.
            #group_sync_ok = self.update_node_groups(groups)
            #groupinfo.save()
            #member_sync_ok = self.update_node_members(members)
            #memberinfo.save()

            group_sync_ok = True
            member_sync_ok = True
            membership_sync_ok = False
            connection_sync_ok = False

            count = 0
            for g in groups:
                count += 1;
                if count >= 38:
                    count = 0
                    self.session = cypher.Session(NEO4J_ROOT_URI)

                memberships = Membership.objects.filter(group=g,
                    lastmodifieddate__lt=membershipinfo.lastupdateddate)

                self.stdout.write("> Group: {0} -- 'Membership' "
                                "updates: {1}".format(g.name, len(memberships)))
                membership_sync_ok = self.update_rel_memberships(memberships)
                connection_sync_ok = self.update_rel_connections(memberships)
            membershipinfo.save()

            if group_sync_ok and member_sync_ok \
               and membership_sync_ok and connection_sync_ok:
                self.stdout.write('[STATUS] Databases are now synchronized.')
            else:
                self.stdout.write('[STATUS] Error encountered during sync. \n'
                                  '> Please check databases for consistency '
                                  'and try again.')
        else:
            self.stdout.write(">>> To execute these updates and synchronize "
                              "the NEO4J database with the SalesForce database, "
                              "re-run commans with '--sync' option.")


    def update_node_groups(self, groups):
        merge_cypher = ('MERGE (node:Group {{ sf_id: "{sf_id}" }}) '
                        'ON CREATE SET node.name = "{name}" '
                        'RETURN node')
        delete_cypher = ('MATCH (node:Group {{ sf_id: "{sf_id}" }})-[rel]-() '
                         'DELETE node, rel')

        try:
            tx = self.session.create_transaction()
            num_removed = 0
            for g in groups:
                if g.is_deleted:
                    self.stdout.write("> REMOVED 'Group' node: {0}".format(
                        g.name))
                    num_removed += 1
                    query = delete_cypher.format(sf_id=g.Id)
                else:
                    # Update or create if none exist.
                    query = merge_cypher.format(sf_id=g.Id, name=g.name)
                tx.append(query)

            # Execute all queries on server and commit transaction.
            group_nodes = tx.commit()
        except cypher.TransactionError as error:
            self.stderr.write('!!!!!!---------TRANSACTION-ERROR---------!!!!!!\n')
            self.stderr.write(str(error))
            return False
        else:
            if tx.finished:
                num_results = len(group_nodes)
                # Nested empty lists returned when no query matches or updates.
                if num_results == 1:
                    num_results = len(group_nodes[0])

                self.stdout.write(">>> [{0}] 'Group' node(s) successfully "
                                  "synced.".format(num_results))
                if num_removed:
                    self.stdout.write(">>> [{0}] 'Group' node(s) removed.".format(
                        num_removed))
                return True


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
                        'RETURN node')
        delete_cypher = ('MATCH (node:Member {{ sf_id: "{sf_id}" }})-[rel]-() '
                         'DELETE node, rel')

        try:
            tx = self.session.create_transaction()
            num_removed = 0
            for m in members:
                if m.is_deleted:
                    self.stdout.write("> REMOVED 'Member' node: {0}".format(
                        m.name))
                    num_removed += 1
                    query = delete_cypher.format(sf_id=m.Id)
                else:
                    # Update or create if none exists.
                    query = merge_cypher.format(sf_id=m.Id, firstname=m.firstname,
                                                lastname=m.lastname, dob=m.dob,
                                                gender=m.gender, race=m.race,
                                                asian_ethnicity=m.asian_ethnicity)
                tx.append(query)

            # Execute all queries on server and commit transaction.
            member_nodes = tx.commit()
        except cypher.TransactionError as error:
            self.stderr.write('!!!!!!---------TRANSACTION-ERROR---------!!!!!!\n')
            self.stderr.write(str(error))
            return False
        else:
            if tx.finished:
                num_results = len(member_nodes)
                # Nested empty lists returned when no query matches or updates.
                if num_results == 1:
                    num_results = len(member_nodes[0])

                self.stdout.write(">>> [{0}] 'Member' node(s) successfully "
                                  "synced.".format(num_results))
                if num_removed:
                    self.stdout.write(">>> [{0}] 'Member' node(s) "
                                      "removed.".format(num_removed))
                return True


    def update_rel_memberships(self, memberships):
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
                        '_is_new: false }} '
                        'RETURN rel')
        delete_cypher = ('MATCH ()-[rel:MEMBER_OF]->() '
                         'WHERE rel.sf_id = "{sf_id}" '
                         'DELETE rel')

        try:
            tx = self.session.create_transaction()
            num_removed = 0
            for r in memberships:
                if r.is_deleted:
                    num_removed += 1
                    query = delete_cypher.format(sf_id=r.Id)
                else:
                    # Rules for dealing with incomplete date information.
                    if r.startdate == None and r.enddate == None:
                        if r.status == 'Current':
                            startyear = 9999
                            endyear = 9999
                        else:
                            startyear = 'null'
                            endyear = 'null'
                    elif r.startdate != None and r.enddate == None:
                        if r.status == 'Current':
                            startyear = r.startdate.year
                            endyear = 9999
                        else:
                            startyear = r.startdate.year
                            endyear = r.startdate.year
                    elif r.startdate == None and r.enddate != None:
                        startyear = r.enddate.year
                        endyear = r.enddate.year
                    elif r.startdate != None and r.enddate != None:
                        startyear = r.startdate.year
                        endyear = r.enddate.year

                    # Update or create if none exists.
                    query = merge_cypher.format(member_id=r.member.Id,
                                                group_id=r.group.Id,
                                                rel_id=r.Id,
                                                status=r.status,
                                                start=startyear,
                                                end=endyear)
                tx.append(query)

            # Execute all queries on server and commit transaction.
            # Save results.
            self.membership_rels = tx.commit()
        except cypher.TransactionError as error:
            self.stderr.write('!!!!!!---------TRANSACTION-ERROR---------!!!!!!\n')
            self.stderr.write(str(error))
            return False
        else:
            if tx.finished:
                num_results = len(self.membership_rels)
                # Nested empty lists returned when no query matches or updates.
                if num_results == 1:
                    num_results = len(self.membership_rels[0])

                self.stdout.write(">>> [{0}] 'Membership' relationship(s) "
                                  "successfully synced.".format(num_results))
                if num_removed:
                    self.stdout.write(">>> [{0}] 'Membership' relationship(s) "
                                      "removed.".format(num_removed))
                return True


    def update_rel_connections(self, memberships):
        findall_cypher = ('MATCH (a:Member)-[r1:MEMBER_OF]->(g:Group), '
                          '(b:Member)-[r2:MEMBER_OF]->(g:Group) '
                          'WHERE NOT a = b AND r1.start <= r2.end '
                          'AND r2.start <= r1.end '
                          'MERGE (a)-[c:CONNECTED_TO {group: g.name}]-(b) '
                          'ON CREATE SET c += {{ '
                          '_a_id: a.sf_id, '
                          '_a_start: r1.start, '
                          '_a_end: r1.end, '
                          '_b_id: b.sf_id, '
                          '_b_start: r2.start, '
                          '_b_end: r2.end }} '
                          'RETURN c')

        ret_cypher = ('MATCH (a:Member {{sf_id: "{a_id}" }})-[c:CONNECTED_TO '
                      '{{group: "{group}" }}]-(b:Member) RETURN c')

        new_cypher = ('MATCH (a:Member '
                      '{{sf_id: "{a_id}" }})-[r1:MEMBER_OF]->(g:Group '
                      '{{sf_id: "{g_id}"}}), '
                      '(b:Member)-[r2:MEMBER_OF]->(g:Group '
                      '{{sf_id: "{g_id}"}}) '
                      'WHERE NOT a = b AND r1.start <= r2.end '
                      'AND r2.start <= r1.end '
                      'MERGE (a)-[c:CONNECTED_TO {{group:g.name}}]-(b) '
                      'ON CREATE SET c += {{ '
                      '_a_id: a.sf_id, '
                      '_a_start: r1.start, '
                      '_a_end: r1.end, '
                      '_b_id: b.sf_id, '
                      '_b_start: r2.start, '
                      '_b_end: r2.end }} '
                      'RETURN c')

        update_cypher = ('MATCH (a:Member {{sf_id: "{a_id}" }})-'
                         '[c:CONNECTED_TO {{group: "{group}" }}]-(b:Member) '
                         'SET c += {{ '
                         '{m_name}: "{a_id}", '
                         '{m_start}: {start}, '
                         '{m_end}: {end} }}')

        delete_cypher = ('MATCH (a:Member {{sf_id: "{a_id}" }})-'
                         '[c:CONNECTED_TO {{group: "{group}" }}]-(b:Member) '
                         'DELETE c')

        try:
            tx = self.session.create_transaction()
            num_removed = 0

            # Check which memberships were deleted, then
            # remove all related connections.
            for r in memberships:
                if r.is_deleted:
                    num_removed += 1
                    query = delete_cypher.format(a_id=r.member.Id,
                                                 group=r.group.name)
                    tx.append(query)

            # Iterate through newly-created/updated memberships and
            # update its corresponding connections.
            for membership_rel in self.membership_rels:
                # Get properties dict from membership Relationship object.
                # This is a HACK for working with Record results from
                # cypher transactions. Due to wrong uri (localhost instead
                # of remote), connection is refused (unresolved bug in py2neo?).
                rel = membership_rel[0][0]._properties

                r = Membership.objects.get(Id=rel['sf_id'])
                if rel['_is_new']:
                    # If newly-added membership relationship,
                    # create new connection relationships.
                    query = new_cypher.format(a_id=r.member.Id, g_id=r.group.Id)
                    tx.append(query)
                else:
                    # If modified and existing membership relationship,
                    # update/delete connection relationships.
                    # Get all connections related to specified membership.
                    ret_query = ret_cypher.format(a_id=r.member.Id,
                                                  group=r.group.name)
                    connections = self.session.execute(ret_query)

                    # For each connection relation, check if updated startyear
                    # endyear still overlap.
                    for connect in connections:
                        # HACK (see above): get properties dict from
                        # connection Relationship object.
                        c = connect[0]._properties

                        # Determine which property member corresponds to,
                        # since connection relationship is undirected.
                        if r.member.Id == c['_a_id']:
                            # Do nothing if dates were not changed.
                            if rel['start'] == c['_a_start'] and \
                               rel['end'] == c['_a_end']:
                                continue
                            else:
                                # Dates still overlap, so update.
                                if rel['start'] <= c['_b_end'] and \
                                   c['_b_start'] <= rel['end']:
                                    query = update_a_cypher.format(m_name="_a_id",
                                        a_id = r.member.Id, group=r.group.name,
                                        m_start="_a_start", m_end="_a_end",
                                        start=rel['start'], end=rel['end'])
                                else:
                                    # Dates no longer overlap, so remove.
                                    query = delete_cypher.format(
                                        a_id=r.member.Id, group=r.group.name)
                        elif r.member.Id == c['_b_id']:
                            if rel['start'] == c['_b_start'] and \
                               rel['end'] == c['_b_end']:
                                continue
                            else:
                                if rel['start'] <= c['_a_end'] and \
                                   c['_a_start'] <= rel['end']:
                                    query = update_a_cypher.format(m_name="_b_id",
                                        a_id=r.member.Id, group=r.group.name,
                                        m_start="_b_start", m_end="_b_end",
                                        start=rel['start'], end=rel['end'])
                                else:
                                    query = delete_cypher.format(
                                        a_id=r.member.Id, group=r.group.name)

                        tx.append(query)

            connection_rels = tx.commit()
        except cypher.TransactionError as error:
            self.stderr.write('!!!!!!---------TRANSACTION-ERROR---------!!!!!!\n')
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
                return True
