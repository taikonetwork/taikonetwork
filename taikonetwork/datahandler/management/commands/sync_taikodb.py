"""
    commands.sync_taikodb
    ----------------------

    Custom management command that synchronizes Taiko Network's
    Neo4j database and SQL database with the Salesforce database.

"""
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import logging

from datahandler.util import sql_updater, neo4j_updater


# Get instance of logger for datahandler management command.
logger = logging.getLogger('datahandler')


class Command(BaseCommand):
    help = ("Synchronizes Taiko Network's Neo4j database and SQL database with "
            "the Salesforce database.")

    option_list = BaseCommand.option_list + (
        make_option('--db',
                    type='choice',
                    action='store',
                    dest='db',
                    choices=['all', 'sql', 'neo4j'],
                    help=("Specified the database to be updated with the "
                          "latest Salesforce data."),
                    metavar='{all, sql, neo4j}'),
    )

    option_list = option_list + (
        make_option('--dry-run',
                    action='store_true',
                    dest='test',
                    default=False,
                    help=("Check for updates to the Salesforce database. "
                          "No updates are executed on the databases; "
                          "only displays the count of newly-added or "
                          "recently-modified objects. No updates are "
                          "executed on the databases.")),
    )

    def handle(self, **options):
        if options['db'] is None:
            raise CommandError("Option `--db={all, sql, neo4j}` must be specified.")

        try:
            self.sql_updater = sql_updater.SqlUpdater()
        except:
            logger.error("SqlUpdater() failed to initialize.")
            raise CommandError("Command failed. Please check the logs.")

        try:
            self.neo4j_updater = neo4j_updater.Neo4jUpdater()
        except:
            logger.error("Neo4jUpdater() failed to initialize.")
            raise CommandError("Command failed. Please check the logs.")

        sql_sync_ok = True
        if options['db'] == 'sql' or options['db'] == 'all':
            sql_sync_ok, updates_found = self._sync_sql_db(options['test'])
            if not options['test'] and updates_found:
                if sql_sync_ok:
                    logger.info(">>> SQL database has been successfully synchronized.")
                else:
                    logger.error(">>> SQL database synchronization has failed. "
                                 "Please inspect logs and database configurations.")

        neo4j_sync_ok = True
        if options['db'] == 'neo4j' or (options['db'] == 'all' and sql_sync_ok):
            neo4j_sync_ok, updates_found = self._sync_neo4j_db(options['test'])
            if not options['test'] and updates_found:
                if neo4j_sync_ok:
                    logger.info(">>> Neo4j database has been successfully synchronized.")
                else:
                    logger.error(">>> Neo4j database synchronization has failed. "
                                 "Please inspect logs and database configurations.")

        if (sql_sync_ok and neo4j_sync_ok and
                options['db'] == 'all' and not options['test']):
            logger.info(">>> All databases are now synchronized.")

    def _sync_sql_db(self, testing):
        logger.info(">>> Checking Salesforce database for updates...")
        num_groups, num_members, num_mships = self.sql_updater.check_salesforce_db()

        logger.info("DATA TO BE SYNCED (from Salesforce DB to SQL DB):"
                    "\n        > 'Account' update count: {0}"
                    "\n        > 'Contact' update count: {1}"
                    "\n        > 'Affiliation' update count: {2}".format(
                        num_groups, num_members, num_mships))

        group_ok, member_ok, mship_ok, updates_found = True, True, True, True
        if not testing:
            # Exit early if no updates found.
            if not num_groups and not num_members and not num_mships:
                updates_found = False
                logger.info(">>> No updates to sync to SQL database.")
                return False, updates_found

            logger.info(">>> Syncing SQL database with Salesforce...")
            if num_groups > 0:
                group_ok = self.sql_updater.update_groups()
            if num_members > 0:
                member_ok = self.sql_updater.update_members()
            if num_mships > 0 and (group_ok and member_ok):
                mship_ok = self.sql_updater.update_memberships()

            if not group_ok:
                logger.error("SQL: Group updates failed to sync.")
            if not member_ok:
                logger.error("SQL: Member updates failed to sync.")
            if not mship_ok:
                logger.error("SQL: Membership updates failed to sync.")

        return (group_ok and member_ok and mship_ok), updates_found

    def _sync_neo4j_db(self, testing):
        logger.info(">>> Checking SQL database for updates...")
        num_groups, num_members, num_mships = self.neo4j_updater.check_sql_db()

        logger.info("DATA TO BE SYNCED (from SQL DB to Neo4j DB):"
                    "\n        > 'Group' update count: {0}"
                    "\n        > 'Member' update count: {1}"
                    "\n        > 'Membership' update count: {2}".format(
                        num_groups, num_members, num_mships))

        group_ok, member_ok, rel_ok, updates_found = True, True, True, True
        if not testing:
            # Exit early if no updates found.
            if not num_groups and not num_members and not num_mships:
                updates_found = False
                logger.info(">>> No updates to sync to Neo4j database.")
                return False, updates_found

            logger.info(">>> Syncing Neo4j database with SQL database...")
            if num_groups > 0:
                group_ok = self.neo4j_updater.update_group_nodes()
            if num_members > 0:
                member_ok = self.neo4j_updater.update_member_nodes()
            if num_mships > 0:
                rel_ok = self.neo4j_updater.batch_update_relationships()

            if not group_ok:
                logger.error("Neo4j: Group updates failed to sync.")
            if not member_ok:
                logger.error("Neo4j: Member updates failed to sync.")
            if not rel_ok:
                logger.error("Neo4j: Membership/Connection updates failed to sync.")

        return (group_ok and member_ok and rel_ok), updates_found
