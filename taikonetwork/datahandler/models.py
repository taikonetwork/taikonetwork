from django.db import models
from salesforce import models as sf_models


# Keeps track of when Neo4j DB was last synced with lastest Salesforce data.
class Neo4jSyncInfo(models.Model):
    model_type = models.CharField(max_length=32)
    lastupdateddate = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '[{0}] {1}'.format(self.model_type, str(self.lastupdateddate))
        # update.strftime('%Y-%m-%d %H:%M:%S.%f%z')


# Keeps track of when PostgreSQL DB was last synced with Salesforce DB.
class SqlSyncInfo(models.Model):
    model_type = models.CharField(max_length=32)
    lastupdateddate = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '[{0}] {1}'.format(self.model_type, str(self.lastupdateddate))


class Group(models.Model):
    sf_id = models.CharField(max_length=30)
    name = models.CharField(max_length=255)
    category = models.CharField(
        max_length=4099,
        choices=[('Professional', 'Professional'), ('Community', 'Community'),
                 ('Collegiate/University', 'Collegiate/University'),
                 ('Youth', 'Youth'), ('Buddhist', 'Buddhist'),
                 ('Classes', 'Classes'), ('Post-Collegiate', 'Post-Collegiate'),
                 ('All Women', 'All Women')],
        blank=True)
    founding_date = models.DateField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    country = models.CharField(max_length=80, blank=True)
    state = models.CharField(max_length=80, blank=True)
    city = models.CharField(max_length=40, blank=True)
    postalcode = models.CharField(max_length=20, blank=True)
    street = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=18, decimal_places=15,
                                   blank=True, null=True)
    longitude = models.DecimalField(max_digits=18, decimal_places=15,
                                    blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    lastmodifieddate = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "[{0}] {1}".format(self.sf_id, self.name)


class Member(models.Model):
    sf_id = models.CharField(max_length=30)
    name = models.CharField(max_length=121)
    firstname = models.CharField(max_length=40)
    lastname = models.CharField(max_length=80)
    email = models.EmailField(blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=255,
                              choices=[('Male', 'Male'), ('Female', 'Female')],
                              blank=True)
    race = models.CharField(
        max_length=4099,
        choices=[('American Indian or Alaska Native', 'American Indian or Alaska Native'),
                 ('Asian or Asian American', 'Asian or Asian American'),
                 ('Pacific Islander or Native Hawaiian', 'Pacific Islander or Native Hawaiian'),
                 ('Black or African American', 'Black or African American'),
                 ('White or Caucasian', 'White or Caucasian'),
                 ('Hispanic or Latino', 'Hispanic or Latino')],
        blank=True)
    asian_ethnicity = models.CharField(
        max_length=4099,
        choices=[('Cambodian', 'Cambodian'), ('Chinese', 'Chinese'),
                 ('Filipino', 'Filipino'), ('Indian', 'Indian'),
                 ('Indonesian', 'Indonesian'), ('Japanese', 'Japanese'),
                 ('Javanese', 'Javanese'), ('Korean', 'Korean'),
                 ('Laotian', 'Laotian'), ('Malaysian', 'Malaysian'),
                 ('Mauritian', 'Mauritian'), ('Okinawan', 'Okinawan'),
                 ('Palestinian', 'Palestinian'), ('Syrian', 'Syrian'),
                 ('Taiwanese', 'Taiwanese'), ('Thai', 'Thai'),
                 ('Vietnamese', 'Vietnamese')],
        blank=True)
    is_deleted = models.BooleanField(default=False)
    lastmodifieddate = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "[{0}] {1}".format(self.sf_id, self.name)


class Membership(models.Model):
    sf_id = models.CharField(max_length=30)
    group = models.ForeignKey(Group, related_name='memberships', on_delete=models.PROTECT)
    member = models.ForeignKey(Member, related_name='memberships', on_delete=models.PROTECT)
    startdate = models.DateField(blank=True, null=True)
    enddate = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=255,
                              choices=[('Current', 'Current'),
                                       ('Former', 'Former')],
                              blank=True)
    is_primary = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    lastmodifieddate = models.DateTimeField(auto_now=True)

    def __str__(self):
        output = ("[{0}] Group: {1}, Member: {2}, Start: {3}, End: {4}")
        return output.format(self.sf_id, self.group.name, self.member.name,
                             str(self.startdate), str(self.enddate))


# -----------------------------------------------------------
# SALESFORCE MODELS
# -----------------------------------------------------------
# SalesForce model: Account (type='Taiko Group') equivalent to Group model.
class Account(sf_models.SalesforceModel):
    name = sf_models.CharField(db_column='Name', max_length=255,
                               verbose_name='Account Name')

    category = sf_models.CharField(
        db_column='Category__c', max_length=4099, verbose_name='Category',
        choices=[('Professional', 'Professional'), ('Community', 'Community'),
                 ('Collegiate/University', 'Collegiate/University'),
                 ('Youth', 'Youth'), ('Buddhist', 'Buddhist'),
                 ('Classes', 'Classes'), ('Post-Collegiate', 'Post-Collegiate'),
                 ('All Women', 'All Women')],
        blank=True)

    founding_date = sf_models.DateField(db_column='Founding_Date__c',
                                        verbose_name='Founding Date',
                                        blank=True, null=True)

    email = sf_models.EmailField(db_column='Email__c', verbose_name='Email',
                                 blank=True, null=True)

    website = sf_models.URLField(db_column='Website', verbose_name='Website',
                                 blank=True, null=True)

    non_us_country = sf_models.CharField(
        db_column='Non_US_Country__c', max_length=1300,
        verbose_name='Non-US Country', sf_read_only=sf_models.READ_ONLY, blank=True)

    country = sf_models.CharField(db_column='BillingCountry', max_length=80,
                                  verbose_name='Billing Country', blank=True)

    state = sf_models.CharField(db_column='BillingState', max_length=80,
                                verbose_name='Billing State/Province', blank=True)

    city = sf_models.CharField(db_column='BillingCity', max_length=40,
                               verbose_name='Billing City', blank=True)

    postalcode = sf_models.CharField(db_column='BillingPostalCode', max_length=20,
                                     verbose_name='Billing Zip/Postal Code', blank=True)

    street = sf_models.TextField(db_column='BillingStreet',
                                 verbose_name='Billing Street', blank=True)

    latitude = sf_models.DecimalField(
        db_column='BillingLatitude', max_digits=18, decimal_places=15,
        verbose_name='Billing Latitude', blank=True, null=True)

    longitude = sf_models.DecimalField(
        db_column='BillingLongitude', max_digits=18, decimal_places=15,
        verbose_name='Billing Longitude', blank=True, null=True)

    accounttype = sf_models.CharField(
        db_column='Type', max_length=40, verbose_name='Account Type',
        choices=[('Individual', 'Individual'), ('Taiko Group', 'Taiko Group'),
                 ('Business', 'Business'), ('Foundation', 'Foundation'),
                 ('Organization', 'Organization'), ('Government', 'Government'),
                 ('Other', 'Other')],
        blank=True)

    is_deleted = sf_models.BooleanField(db_column='IsDeleted', verbose_name='Deleted',
                                        sf_read_only=sf_models.READ_ONLY)

    lastmodifieddate = sf_models.DateTimeField(db_column='LastModifiedDate',
                                               verbose_name='Last Modified Date',
                                               sf_read_only=sf_models.READ_ONLY)

    class Meta(sf_models.SalesforceModel.Meta):
        db_table = 'Account'
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'
        # keyPrefix = '001'
        managed = False


# SalesForce model: Contact equivalent to Member model.
class Contact(sf_models.SalesforceModel):
    name = sf_models.CharField(db_column='Name', max_length=121,
                               verbose_name='Full Name',
                               sf_read_only=sf_models.READ_ONLY)

    firstname = sf_models.CharField(db_column='FirstName', max_length=40,
                                    verbose_name='First Name', blank=True)

    lastname = sf_models.CharField(db_column='LastName', max_length=80,
                                   verbose_name='Last Name')

    email_readonly = sf_models.EmailField(
        db_column='Email', verbose_name='Email',
        help_text="The Nonprofit Starter Pack fills this field from the \
                   other email fields on Contact. You shouldn't edit this field \
                   directly if you have the Preferred Email workflow rules enabled.",
        blank=True, null=True)

    email_writable = sf_models.EmailField(db_column='npe01__HomeEmail__c',
                                          verbose_name='Personal Email',
                                          blank=True, null=True)

    dob = sf_models.DateField(db_column='Birthdate', verbose_name='Birthdate',
                              blank=True, null=True)

    age_group = sf_models.CharField(
        db_column='Age_Group__c', max_length=255, verbose_name='Age Group',
        choices=[('10 or under', '10 or under'), ('11-17', '11-17'),
                 ('18-25', '18-25'), ('26-30', '26-30'), ('31-39', '31-39'),
                 ('40-49', '40-49'), ('50-59', '50-59'), ('60-69', '60-69'),
                 ('70+', '70+')],
        blank=True)

    gender = sf_models.CharField(
        db_column='Gender__c', max_length=255, verbose_name='Gender',
        choices=[('Male', 'Male'), ('Female', 'Female')], blank=True)

    race = sf_models.CharField(
        db_column='Race__c', max_length=4099, verbose_name='Race',
        choices=[('American Indian or Alaska Native', 'American Indian or Alaska Native'),
                 ('Asian or Asian American', 'Asian or Asian American'),
                 ('Pacific Islander or Native Hawaiian', 'Pacific Islander or Native Hawaiian'),
                 ('Black or African American', 'Black or African American'),
                 ('White or Caucasian', 'White or Caucasian'),
                 ('Hispanic or Latino', 'Hispanic or Latino')],
        blank=True)

    asian_ethnicity = sf_models.CharField(
        db_column='Asian_Ethnicity__c', max_length=4099, verbose_name='Asian Ethnicity',
        choices=[('Cambodian', 'Cambodian'), ('Chinese', 'Chinese'),
                 ('Filipino', 'Filipino'), ('Indian', 'Indian'),
                 ('Indonesian', 'Indonesian'), ('Japanese', 'Japanese'),
                 ('Javanese', 'Javanese'), ('Korean', 'Korean'),
                 ('Laotian', 'Laotian'), ('Malaysian', 'Malaysian'),
                 ('Mauritian', 'Mauritian'), ('Okinawan', 'Okinawan'),
                 ('Palestinian', 'Palestinian'), ('Syrian', 'Syrian'),
                 ('Taiwanese', 'Taiwanese'), ('Thai', 'Thai'),
                 ('Vietnamese', 'Vietnamese')],
        blank=True)

    is_deleted = sf_models.BooleanField(
        db_column='IsDeleted', verbose_name='Deleted', sf_read_only=sf_models.READ_ONLY)

    lastmodifieddate = sf_models.DateTimeField(db_column='LastModifiedDate',
                                               verbose_name='Last Modified Date',
                                               sf_read_only=sf_models.READ_ONLY)

    class Meta(sf_models.SalesforceModel.Meta):
        db_table = 'Contact'
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'
        # keyPrefix = '003'
        managed = False


# SalesForce model: Affiliation is equivalent to Membership model.
class Affiliation(sf_models.SalesforceModel):
    name = sf_models.CharField(db_column='Name', max_length=80,
                               verbose_name='Afilliation Name',
                               sf_read_only=sf_models.READ_ONLY)

    group = sf_models.ForeignKey(Account, sf_read_only=sf_models.NOT_UPDATEABLE,
                                 on_delete=sf_models.PROTECT,
                                 db_column='npe5__Organization__c')

    member = sf_models.ForeignKey(Contact, sf_read_only=sf_models.NOT_UPDATEABLE,
                                  on_delete=sf_models.PROTECT,
                                  db_column='npe5__Contact__c')

    startdate = sf_models.DateField(db_column='npe5__StartDate__c',
                                    verbose_name='Start Date',
                                    blank=True, null=True)

    enddate = sf_models.DateField(db_column='npe5__EndDate__c',
                                  verbose_name='End Date',
                                  blank=True, null=True)

    status = sf_models.CharField(db_column='npe5__Status__c', max_length=255,
                                 verbose_name='Status',
                                 choices=[('Current', 'Current'),
                                          ('Former', 'Former')],
                                 blank=True)

    is_primary = sf_models.BooleanField(db_column='Primary_Group__c',
                                        verbose_name='Primary Group')

    is_deleted = sf_models.BooleanField(db_column='IsDeleted', verbose_name='Deleted',
                                        sf_read_only=sf_models.READ_ONLY)

    lastmodifieddate = sf_models.DateTimeField(db_column='LastModifiedDate',
                                               verbose_name='Last Modified Date',
                                               sf_read_only=sf_models.READ_ONLY)

    createddate = sf_models.DateTimeField(db_column='CreatedDate',
                                          verbose_name='Created Date',
                                          sf_read_only=sf_models.READ_ONLY)

    class Meta(sf_models.SalesforceModel.Meta):
        db_table = 'npe5__Affiliation__c'
        verbose_name = 'Affiliation'
        verbose_name_plural = 'Affilitions'
        # keyPrefix = 'a0C'
        managed = False
