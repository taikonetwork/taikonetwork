"""
    datahandler.util.sql_updater
    ------------------------------

    This module checks for updates to Salesforce and
    synchronizes the managed SQL database with the latest
    Salesforce data.

"""
from django.db import DatabaseError
from django.core.exceptions import ObjectDoesNotExist
import requests
import time
import logging

from datahandler.models import (Account, Contact, Affiliation,
                                Group, Member, Membership, SqlSyncInfo)
from taikonetwork.authentication import GEOCODE_API_KEY


# Get instance of logger for SqlUpdater.
logger = logging.getLogger('datahandler.sql_updater')


class SqlUpdater:
    def __init__(self):
        try:
            self.groupinfo = SqlSyncInfo.objects.get(model_type='Group')
            self.memberinfo = SqlSyncInfo.objects.get(model_type='Member')
            self.mshipinfo = SqlSyncInfo.objects.get(model_type='Membership')
        except SqlSyncInfo.DoesNotExist as error:
            logger.error('SqlSyncInfo object does no exist.')
            raise Exception(error)

    def check_salesforce_db(self):
        num_accounts = Account.objects.filter(
            accounttype='Taiko Group',
            lastmodifieddate__gt=self.groupinfo.lastupdateddate).count()
        num_contacts = Contact.objects.filter(
            lastmodifieddate__gt=self.memberinfo.lastupdateddate).count()
        num_affiliations = Affiliation.objects.filter(
            lastmodifieddate__gt=self.mshipinfo.lastupdateddate).count()

        return num_accounts, num_contacts, num_affiliations

    def update_groups(self):
        try:
            new_groups = Account.objects.filter(
                accounttype='Taiko Group',
                lastmodifieddate__gt=self.groupinfo.lastupdateddate)
        except DatabaseError as db_error:
            logger.error(db_error)
            return False
        except:
            logger.exception("Group: unexpected error encountered.")
            return False

        num_added, num_updated = 0, 0
        for g in new_groups:
            updated_values = {
                'name': g.name,
                'category': self._xstr(g.category),
                'founding_date': g.founding_date,
                'email': g.email,
                'website': g.website,
                'is_deleted': g.is_deleted
            }
            address = {'country': self._xstr(g.country),
                       'state': self._xstr(g.state),
                       'city': self._xstr(g.city),
                       'postalcode': self._xstr(g.postalcode),
                       'street': self._xstr(g.street)}

            try:
                (group, created) = Group.objects.update_or_create(
                    sf_id=g.id, defaults=updated_values)
                self._update_location_data(group, address)

                if created:
                    num_added += 1
                    logger.debug("Added new group: {0}".format(group.name))
                else:
                    num_updated += 1
                    logger.debug("Updated existing group: {0}".format(group.name))
            except:
                logger.exception("Group: unexpected error encountered.")
                return False

        self.groupinfo.save()
        logger.info("> [SYNC OK] Group: ({0}) added, ({1}) updated.".format(
            num_added, num_updated))
        return True

    def _update_location_data(self, group, address):
        """Check if address has changed; if so, update geocoordinates.
           Get geocoordinates for newly-added groups only if address
           information provided.

        """
        if (address['country'] != group.country
                or address['state'] != group.state
                or address['city'] != group.city
                or address['postalcode'] != group.postalcode
                or address['street'] != group.street):
            # Call Geocoding API only if unique address information available.
            if address['city'] or address['postalcode'] or address['street']:
                latitude, longitude = self.get_geocoordinates(group.name, address)
                address['latitude'] = latitude
                address['longitude'] = longitude

                for key, value in address.items():
                    setattr(group, key, value)
                group.save()

    def get_geocoordinates(self, name, address):
        """Get geocoordinates.
            Reference: https://developers.google.com/maps/documentation/geocoding/

        """
        geocode_url = 'https://maps.googleapis.com/maps/api/geocode/json?{address}&key={key}'
        address_str = 'address={street}{city}{state}{postalcode}{country}'
        latitude, longitude = None, None
        make_request = True
        num_requests = 0
        request_limit = 5

        street, city, state, country, postalcode = '', '', '', '', ''
        if address['street']:
            street = address['street']
        if address['city']:
            city = ', ' + address['city']
        if address['state']:
            state = ', ' + address['state']
        if address['postalcode']:
            postalcode = ' ' + address['postalcode']
        if address['country']:
            country = ', ' + address['country']

        req_addr = address_str.format(street=street, city=city, state=state,
                                      postalcode=postalcode, country=country)
        req_addr = req_addr.replace(' ', '+')
        req_addr = req_addr.replace('address=,+', 'address=')

        while make_request and (num_requests < request_limit):
            url = geocode_url.format(address=req_addr, key=GEOCODE_API_KEY)
            r = requests.get(url)
            num_requests += 1

            try:
                if r.status_code == 200:
                    data = r.json()
                    if data['status'] == 'OK':
                        coordinates = data['results'][0]['geometry']['location']
                        latitude = coordinates.get('lat', None)
                        longitude = coordinates.get('lng', None)

                    elif data['status'] == 'INVALID_REQUEST':
                        # P.O. Box not supported; remove street address and try again.
                        if street:
                            logger.warning(
                                "Gecoding API - Invalid Request: <{}>. "
                                "Re-trying w/o street address...".format(name))
                            street = ''
                            req_addr = address_str.format(
                                street=street, city=city, state=state,
                                postalcode=postalcode, country=country)
                            req_addr = req_addr.replace(' ', '+')
                            req_addr = req_addr.replace('address=,+', 'address=')
                            continue

                    elif data['status'] == 'OVER_QUERY_LIMIT':
                        # Usage Limits: 2,500 reqs/24hrs or 5 reqs/sec.
                        logger.warning("Geocoding API - Rate-limit Exceeded. "
                                       "Re-trying in 5 seconds...")
                        time.sleep(5)
                        continue

                    elif data['status'] == 'UNKNOWN_ERROR':
                        logger.warning("Geocoding API - Server Error. "
                                       "Re-trying in 5 seconds...")
                        time.sleep(5)
                        continue

                    else:
                        logger.warning("Geocoding API - No Results / "
                                       "Request Denied: <{}>".format(name))
                else:
                    logger.error("Geocoding API - Request Failed: <{}>".format(name))
                    logger.debug("Request STATUS: {0} \nURL: {1} \nJSON: {2}".format(
                        r.status_code, url, r.text))

                make_request = False
            except:
                logger.error("Geocoding API - Unexpected Error: <{}>".format(name))
                logger.debug("Request STATUS: {0} \nURL: {1} \nJSON: {2}".format(
                    r.status_code, url, r.text))
                make_request = False

        return latitude, longitude

    def update_members(self):
        try:
            new_members = Contact.objects.filter(
                lastmodifieddate__gt=self.memberinfo.lastupdateddate)
        except DatabaseError as db_error:
            logger.error(db_error)
            return False
        except:
            logger.exception("Member: unexpected error encountered.")
            return False

        num_added, num_updated = 0, 0
        for m in new_members:
            updated_values = {
                'name': m.name,
                'firstname': m.firstname,
                'lastname': m.lastname,
                'email': m.email_readonly,
                'dob': m.dob,
                'gender': self._xstr(m.gender),
                'race': self._xstr(m.race),
                'asian_ethnicity': self._xstr(m.asian_ethnicity),
                'is_deleted': m.is_deleted
            }

            try:
                (member, created) = Member.objects.update_or_create(
                    sf_id=m.id, defaults=updated_values)

                if created:
                    num_added += 1
                    logger.debug("Added new member: {0}".format(member.name))
                else:
                    num_updated += 1
                    logger.debug("Updated existing member: {0}".format(member.name))
            except:
                logger.exception("Member: unexpected error encountered.")
                return False

        self.memberinfo.save()
        logger.info("> Member: ({0}) added, ({1}) updated.".format(
            num_added, num_updated))
        return True

    def update_memberships(self):
        try:
            new_memberships = Affiliation.objects.filter(
                lastmodifieddate__gt=self.mshipinfo.lastupdateddate)
        except DatabaseError as db_error:
            logger.error(db_error)
            return False
        except:
            logger.exception("Membership: unexpected error encountered.")
            return False

        num_added, num_updated = 0, 0
        for s in new_memberships:
            try:
                group = Group.objects.get(sf_id=s.group_id)
                member = Member.objects.get(sf_id=s.member_id)
            except ObjectDoesNotExist:
                logger.debug("Membership <{0}> cannot be created. "
                             "Group or Member does not exist in "
                             "SQL database.".format(s.id))
                group = None
                member = None

            if group and member:
                startdate = s.startdate
                if startdate is None:
                    startdate = "{}-01-01".format(s.createddate.year)

                updated_values = {
                    'group': group,
                    'member': member,
                    'startdate': startdate,
                    'enddate': s.enddate,
                    'status': self._xstr(s.status),
                    'is_primary': s.is_primary,
                    'is_deleted': s.is_deleted
                }

                try:
                    (mship, created) = Membership.objects.update_or_create(
                        sf_id=s.id, defaults=updated_values)

                    if created:
                        num_added += 1
                    else:
                        num_updated += 1
                except:
                    logger.exception("Membership: unexpected error encountered.")
                    return False

        self.mshipinfo.save()
        logger.info("> [SYNC OK] Membership: ({0}) added, ({1}) updated.".format(
            num_added, num_updated))
        return True

    def _xstr(self, s):
        if s is None:
            return ''
        return str(s)
