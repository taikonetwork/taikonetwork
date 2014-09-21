import csv
from datetime import datetime

from datahandler.models import GroupAlt
from taikonetwork.api_authentication import GEOCODE_API_KEY
import requests


def format_csv():
    # Id = 0, IsDeleted = 1, Name = 3, Type = 4
    # BillingStreet = 6, BillingCity = 7, BillingState = 8
    # BillingPostalCode = 9, BillingCountry = 10
    # BillingLatitude = 11, BillingLongitude = 12
    # Website = 23, LastModifiedDate = 36, Founding_Date__c = 78
    # Category__c = 79, Email__c = 82

    with open('data/taiko_groups.csv', 'w', newline='') as output:
        writer = csv.writer(output, delimiter=',', quoting=csv.QUOTE_MINIMAL)

        with open('group_data/groups.csv', 'r', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            i = 0
            try:
                for r in reader:
                    if r[4] == 'Taiko Group':
                        writer.writerow(
                            [r[0], r[1], r[3], r[4], r[6], r[7], r[8], r[9],
                             r[10], r[11], r[12], r[23], r[36], r[78], r[79], r[82]])
                    i += 1
            except:
                print('Error at line: {}'.format(i))


def load_to_db():
    with open('data/taiko_groups.csv', 'r', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for r in reader:
            sf_id = r[0]
            is_deleted = int(r[1])
            name = r[2]
            accounttype = r[3]
            street = r[4]
            city = r[5]
            state = r[6]
            postalcode = r[7]
            country = r[8]
            # latitude=r[9]
            # longitude=r[10]
            website = r[11]
            lastmodifieddate = datetime.strptime(r[12], '%Y-%m-%d %H:%M:%S')
            if r[13]:
                founding_date = datetime.strptime(r[13], '%Y-%m-%d %H:%M:%S')
            else:
                founding_date = None
            category = r[14]
            email = r[15]

            try:
                g = GroupAlt.objects.get(sf_id=sf_id, name=name)
                GroupAlt.objects.filter(sf_id=sf_id).update(
                    is_deleted=is_deleted,
                    accounttype=accounttype, street=street, city=city,
                    state=state, postalcode=postalcode, country=country,
                    website=website, lastmodifieddate=lastmodifieddate,
                    founding_date=founding_date, category=category,
                    email=email)
            except GroupAlt.DoesNotExist:
                g = GroupAlt(sf_id=sf_id, is_deleted=is_deleted, name=name,
                             accounttype=accounttype, street=street, city=city,
                             state=state, postalcode=postalcode, country=country,
                             website=website, lastmodifieddate=lastmodifieddate,
                             founding_date=founding_date, category=category,
                             email=email)
                g.save()


def get_geocoordinates(groupname=None):
    geocode_url = 'https://maps.googleapis.com/maps/api/geocode/json?{address}&key={key}'
    address = 'address={street}{city}{state}{postalcode}{country}'
    make_request = True

    if groupname:
        groups = GroupAlt.objects.filter(name=groupname)
    else:
        groups = GroupAlt.objects.all()

    for g in groups:
        street, city, state, country, postalcode = '', '', '', '', ''
        if g.street:
            street = g.street
        if g.city:
            city = ', ' + g.city
        if g.state:
            state = ', ' + g.state
        if g.postalcode:
            postalcode = ' ' + g.postalcode
        if g.country:
            country = ', ' + g.country

        req_addr = address.format(street=street, city=city, state=state,
                                  postalcode=postalcode, country=country)
        req_addr = req_addr.replace(' ', '+')
        req_addr = req_addr.replace('address=,+', 'address=')

        while make_request:
            url = geocode_url.format(address=req_addr, key=GEOCODE_API_KEY)
            r = requests.get(url)

            try:
                if r.status_code == 200:
                    data = r.json()
                    coordinates = data['results'][0]['geometry']['location']
                    lat = coordinates['lat']
                    lng = coordinates['lng']
                    g.latitude = lat
                    g.longitude = lng
                    g.save()
                else:
                    print('ERROR request failed: [{}]'.format(g.name))
                    print('STATUS: {} \n{}'.format(r.status_code, r.text))
                make_request = False
            except:
                print('ERROR parsing JSON reponse: [{}]. Trying again...'.format(g.name))
                print(url)
                print(r.text)
                # Geocode API cannot find P.O./Mail Box street addresses,
                # so remove street and try again.
                if street:
                    street = ''
                    req_addr = address.format(street=street, city=city, state=state,
                                              postalcode=postalcode, country=country)
                    req_addr = req_addr.replace(' ', '+')
                    req_addr = req_addr.replace('address=,+', 'address=')
                    continue
                else:
                    make_request = False
