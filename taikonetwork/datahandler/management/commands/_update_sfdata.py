from django.core.management.base import BaseCommand
from optparse import make_option
import time
import sys
import math

from datahandler.models import Group, Member, Membership, SyncInfo
from datahandler.tools.neo4j_updater import Neo4jUpdater


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
                groups, members, mships = self._query_updated_data(
                    groupinfo.lastupdateddate,
                    memberinfo.lastupdateddate,
                    membershipinfo.lastupdateddate)

                num_groups = len(groups)
                num_members = len(members)
                # Format Membership queryset to dictionary for easier updating
                # and for reducing SalesForce API calls.
                group_mships, num_mships = self._format_membership_data(mships)

                self.stdout.write("> 'Group' update count: {}".format(num_groups))
                self.stdout.write("> 'Member' update count: {}".format(num_members))
                self.stdout.write("> 'Membership' update count: {}".format(num_mships))

                self.stdout.write('> Syncing SalesForce and NEO4J databases...')
                # Connect session using root service uri for Cypher transactions.
                self.neo4j = Neo4jUpdater()

                # Update nodes and relationships.
                # Set SyncInfo to latest date on proper sync.
                group_ok = True
                if num_groups > 0:
                    (group_ok, group_msg) = self.neo4j.update_node_groups(groups)
                    if group_ok:
                        groupinfo.save()
                    self.stdout.write(group_msg)

                member_ok = True
                if num_members > 0:
                    (member_ok, member_msg) = self.neo4j.update_node_members(members)
                    if member_ok:
                        memberinfo.save()
                    self.stdout.write(member_msg)

                # Membership and Connection relationships dependent on nodes.
                # Sync relationships only if Group and Member nodes updated error-free.
                rel_ok = True
                if group_ok and member_ok and num_mships > 0:
                    rel_ok = self._batch_update_relationships(group_mships)
                    if rel_ok:
                        membershipinfo.save()

                if group_ok and member_ok and rel_ok:
                    end = time.time()
                    self.stdout.write('[STATUS] Databases are now synchronized.\n')
                    self.stdout.write(time.strftime(
                        'Elapsed Time: %M minutes %S seconds.',
                        time.gmtime(end - start)))
                else:
                    self.stdout.write('[STATUS] Error encountered during sync. \n'
                                      '> Please check logs and databases '
                                      'and try again.')
            except:
                self.stderr.write('! --- UNEXPECTED ERROR ENCOUNTERED --- !\n')
                self.stderr.write(sys.exc_info()[0])
                raise
        else:
            num_groups = Group.objects.filter(
                accounttype='Taiko Group',
                lastmodifieddate__lt=groupinfo.lastupdateddate).count()
            num_members = Member.objects.filter(
                lastmodifieddate__lt=memberinfo.lastupdateddate).count()
            num_mships = Membership.objects.filter(
                lastmodifieddate__lt=membershipinfo.lastupdateddate).count()

            self.stdout.write("> 'Group' update count: {}".format(num_groups))
            self.stdout.write("> 'Member' update count: {}".format(num_members))
            self.stdout.write("> 'Membership' update count: {}".format(num_mships))

            self.stdout.write(">>> To execute these updates and synchronize "
                              "the NEO4J database with the SalesForce database, "
                              "re-run commans with '--sync' option.")

    def _query_updated_data(self, group_updatedate, member_updatedate,
                            membership_updatedate):
        groups = Group.objects.filter(
            accounttype='Taiko Group',
            lastmodifieddate__lt=group_updatedate).values(
                'Id', 'name', 'is_deleted')
        members = Member.objects.filter(
            lastmodifieddate__lt=member_updatedate).values(
                'Id', 'firstname', 'lastname', 'dob', 'gender',
                'race', 'asian_ethnicity', 'is_deleted')
        mships = Membership.objects.filter(
            lastmodifieddate__lt=membership_updatedate)

        return groups, members, mships

    def _format_membership_data(self, mships):
        """Format list of Membership dictionaries as a dictionary of
            dictionaries keyed by group id. Allows for updating relationships
            (Memberships and Connections) ona group-by-group basis rather than
            by iterating through each individual membership.

        """
        group_mships = {}
        num_mships = 0
        for s in mships:
            num_mships += 1
            # Rules for dealing with incomplete date information.
            if s.startdate is None and s.enddate is None:
                if s.status == 'Current':
                    startyear = 9999
                    endyear = 9999
                else:
                    startyear = 'null'
                    endyear = 'null'
            elif s.startdate is None and s.enddate is not None:
                startyear = s.enddate.year
                endyear = s.enddate.year
            elif s.startdate is not None and s.enddate is None:
                if s.status == 'Current':
                    startyear = s.startdate.year
                    endyear = 9999
                else:
                    startyear = s.startdate.year
                    endyear = s.startdate.year
            elif s.startdate is not None and s.enddate is not None:
                startyear = s.startdate.year
                endyear = s.enddate.year

            membership_dict = {'member_id': s.member_id,
                               'group_id': s.group_id,
                               'status': s.status,
                               'start': startyear,
                               'end': endyear,
                               'is_deleted': s.is_deleted}

            added = group_mships.get(s.group_id, None)
            if added:
                group_mships[s.group_id][s.Id] = membership_dict
            else:
                group_mships[s.group_id] = {s.Id: membership_dict}

        # Query list of official Taiko Groups
        # (since there are other types of organizations in salesforce)
        taiko_groups = Group.objects.filter(
            accounttype='Taiko Group').values('Id')
        # Check list of dicts to see if membership is for official taiko group.
        group_id_list = list(group_mships.keys())
        for group_id in group_id_list:
            if not any(group['Id'] == group_id for group in taiko_groups):
                num_mships -= len(group_mships[group_id])
                del group_mships[group_id]

        return group_mships, num_mships

    def _batch_update_relationships(self, group_mships):
        """Update Membership and Connection relationships for
            each group consecutively (rather than updating all
            Memberships first, then updating all Connections).
            This is more efficient because the size of transacations
            are smaller and less queries are needed because the updated
            Membership relationships can be saved to memory and used to update
            the Connection relationships.

        """
        total_mships = 0
        total_mships_removed = 0
        total_connections = 0
        total_connect_removed = 0

        for group, memberships in group_mships.items():
            mship_status = self.neo4j.update_rel_memberships(memberships)
            if mship_status[0]:
                total_mships += mship_status[1]
                total_mships_removed += mship_status[2]
                if mship_status[2]:
                    self.stdout.write('- GROUP: ["{0}"] --- # Memberships: '
                                      '{1}, # Removed: {2}'.format(
                                          group, mship_status[1], mship_status[2]))
                else:
                    self.stdout.write('- GROUP: ["{0}"] --- # Memberships: '
                                      '{1}'.format(group, mship_status[1]))

                if mship_status[1]:
                    connect_status = self.neo4j.update_rel_connections(memberships)
                    if connect_status[0]:
                        connect_count = self._nCr(connect_status[1], 2)
                        total_connections += connect_count
                        total_connect_removed += connect_status[2]

                        if connect_status[2]:
                            self.stdout.write('- GROUP: ["{0}"] --- # Connections: '
                                              '{1}, # Removed: {2}'.format(
                                                  group, connect_count,
                                                  connect_status[2]))
                        else:
                            self.stdout.write('- GROUP: ["{0}"] --- # Connections: '
                                              '{1}'.format(group, connect_count))
                    else:
                        self.stderr.write('! --- ERROR --- ! GROUP: ["{0}"]:\n'
                                          '{0}'.format(connect_status[1]))
                        return False
            else:
                self.stderr.write('! --- ERROR --- ! GROUP: ["{0}"]:\n'
                                  '{0}'.format(mship_status[1]))
                return False

        self.stdout.write(">>> [{0}] 'Membership' relationship(s) "
                          "successfully synced.".format(total_mships))
        if total_mships_removed:
            self.stdout.write(">>> [{0}] 'Membership' relationship(s) "
                              "removed.".format(total_mships_removed))
        self.stdout.write(">>> [{0}] 'Connection' relationship(s) "
                          "successfully synced.".format(total_connections))
        if total_connect_removed:
            self.stdout.write(">>> [{0}] 'Connection' relationship(s) "
                              "removed.".format(total_connect_removed))
        return True

    def _nCr(self, n, r):
        if r > 0 and n >= r:
            f = math.factorial
            return int(f(n) / f(r) / f(n - r))
        return 0
