# Logging Tests
import logging
from django.core.exceptions import ObjectDoesNotExist
from datahandler.models import SqlSyncInfo

main_logger = logging.getLogger('datahandler')
sql_logger = logging.getLogger('datahandler.sql_updater')
neo4j_logger = logging.getLogger('datahandler.neo4j_updater')


def test_main_logger():
    main_logger.debug('This is a DEBUG message.')
    main_logger.info('This is an INFO message.')
    main_logger.error('This is an ERROR message.')
    try:
        sqlinfo = SqlSyncInfo.objects.get(model_type='Group')        
    except ObjectDoesNotExist as err:
        main_logger.error("Error message: {0}".format(err))


def test_sql_logger():
    sql_logger.debug('This is a DEBUG message.')
    sql_logger.info('This is an INFO message.')
    sql_logger.error('This is an ERROR message.')

    try:
        inf = 1 / 0
        print(inf)
    except:
        sql_logger.exception('Unexpected error encountered.')


def test_neo4j_logger():
    neo4j_logger.debug('This is a DEBUG message.')
    neo4j_logger.info('This is an INFO message.')
    neo4j_logger.error('This is an ERROR message.')
