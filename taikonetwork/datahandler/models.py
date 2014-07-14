from salesforce import models
import django.db.models


# SalesForce model: Account (type = 'Taiko Group')
class Group(models.SalesforceModel):
    name = models.CharField(db_column='Name', max_length=255, verbose_name=\
                'Account Name')

    category = models.CharField(db_column='Category__c', max_length=4099, \
                verbose_name='Category', choices=\
                [('Professional', 'Professional'), ('Community', 'Community'), \
                 ('Collegiate/University', 'Collegiate/University'), \
                 ('Youth', 'Youth'), ('Buddhist', 'Buddhist'), \
                 ('Classes', 'Classes'), ('Post-Collegiate', 'Post-Collegiate'),\
                 ('All Women', 'All Women')], blank=True)

    founding_date = models.DateField(db_column='Founding_Date__c', verbose_name=\
                'Founding Date', blank=True, null=True)

    email = models.EmailField(db_column='Email__c', verbose_name='Email', \
                blank=True, null=True)

    website = models.URLField(db_column='Website', verbose_name='Website', \
                blank=True, null=True)

    non_us_country = models.CharField(db_column='Non_US_Country__c', \
                max_length=1300, verbose_name='Non-US Country', \
                sf_read_only=models.READ_ONLY, blank=True)

    country = models.CharField(db_column='BillingCountry', max_length=80, \
                verbose_name='Billing Country', blank=True)

    state = models.CharField(db_column='BillingState', max_length=80, \
                verbose_name='Billing State/Province', blank=True)

    city = models.CharField(db_column='BillingCity', max_length=40, \
                verbose_name='Billing City', blank=True)

    postalcode = models.CharField(db_column='BillingPostalCode', max_length=20, \
                verbose_name='Billing Zip/Postal Code', blank=True)

    street = models.TextField(db_column='BillingStreet', \
                verbose_name='Billing Street', blank=True)

    accounttype = models.CharField(db_column='Type', max_length=40, \
                verbose_name='Account Type', choices=\
                [('Individual', 'Individual'), ('Taiko Group', 'Taiko Group'), \
                 ('Business', 'Business'), ('Foundation', 'Foundation'), \
                 ('Organization', 'Organization'), ('Government', 'Government'),\
                 ('Other', 'Other')], blank=True)

    is_deleted = models.BooleanField(db_column='IsDeleted', verbose_name='Deleted', \
                sf_read_only=models.READ_ONLY)

    lastmodifieddate = models.DateTimeField(db_column='LastModifiedDate', \
                verbose_name='Last Modified Date', sf_read_only=models.READ_ONLY)

    class Meta(models.SalesforceModel.Meta):
        db_table = 'Account'
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'
        # keyPrefix = '001'
        managed = False


# SalesForce model: Contact
class Member(models.SalesforceModel):
#    sfaccount = models.ForeignKey(Group, related_name='contact_account_set', \
#                db_column='AccountId', on_delete=models.PROTECT, \
#                blank=True, null=True)
    name = models.CharField(db_column='Name', max_length=121, verbose_name=\
                'Full Name', sf_read_only=models.READ_ONLY)

    firstname = models.CharField(db_column='FirstName', max_length=40, \
                verbose_name='First Name', blank=True)

    lastname = models.CharField(db_column='LastName', max_length=80, \
                verbose_name='Last Name')

    email_readonly = models.EmailField(db_column='Email', verbose_name='Email', \
                help_text="The Nonprofit Starter Pack fills this field from the \
                other email fields on Contact. You shouldn't edit this field \
                directly if you have the Preferred Email workflow rules enabled.", \
                blank=True, null=True)

    email_writable = models.EmailField(db_column='npe01__HomeEmail__c', \
                verbose_name='Personal Email', blank=True, null=True)

    dob = models.DateField(db_column='Birthdate', verbose_name='Birthdate', \
                blank=True, null=True)

    age_group = models.CharField(db_column='Age_Group__c', max_length=255, \
                verbose_name='Age Group', choices=\
                [('10 or under', '10 or under'), ('11-17', '11-17'), \
                 ('18-25', '18-25'), ('26-30', '26-30'), ('31-39', '31-39'), \
                 ('40-49', '40-49'), ('50-59', '50-59'), ('60-69', '60-69'), \
                 ('70+', '70+')], blank=True)

    gender = models.CharField(db_column='Gender__c', max_length=255, \
                verbose_name='Gender', choices=[('Male', 'Male'), \
                ('Female', 'Female')], blank=True)

    race = models.CharField(db_column='Race__c', max_length=4099, \
                verbose_name='Race', choices=[
                ('American Indian or Alaska Native', \
                'American Indian or Alaska Native'), ('Asian or Asian American', \
                'Asian or Asian American'), ('Pacific Islander or Native Hawaiian', \
                'Pacific Islander or Native Hawaiian'), \
                ('Black or African American', 'Black or African American'), \
                ('White or Caucasian', 'White or Caucasian'), \
                ('Hispanic or Latino', 'Hispanic or Latino')], blank=True)

    asian_ethnicity = models.CharField(db_column='Asian_Ethnicity__c', \
                max_length=4099, verbose_name='Asian Ethnicity', choices=[\
                ('Cambodian', 'Cambodian'), ('Chinese', 'Chinese'), \
                ('Filipino', 'Filipino'), ('Indian', 'Indian'), \
                ('Indonesian', 'Indonesian'), ('Japanese', 'Japanese'), \
                ('Javanese', 'Javanese'), ('Korean', 'Korean'), \
                ('Laotian', 'Laotian'), ('Malaysian', 'Malaysian'), \
                ('Mauritian', 'Mauritian'), ('Okinawan', 'Okinawan'), \
                ('Palestinian', 'Palestinian'), ('Syrian', 'Syrian'), \
                ('Taiwanese', 'Taiwanese'), ('Thai', 'Thai'), ('Vietnamese', \
                'Vietnamese')], blank=True)

    is_deleted = models.BooleanField(db_column='IsDeleted', \
                verbose_name='Deleted', sf_read_only=models.READ_ONLY)

    lastmodifieddate = models.DateTimeField(db_column='LastModifiedDate', \
                verbose_name='Last Modified Date', sf_read_only=models.READ_ONLY)

    class Meta(models.SalesforceModel.Meta):
        db_table = 'Contact'
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'
        # keyPrefix = '003'
        managed = False


# SalesForce model: Affiliation
class Membership(models.SalesforceModel):
    name = models.CharField(db_column='Name', max_length=80, verbose_name=\
            'Afilliation Name', sf_read_only=models.READ_ONLY)

    group = models.ForeignKey(Group, sf_read_only=models.NOT_UPDATEABLE, \
            on_delete=models.PROTECT, db_column='npe5__Organization__c')

    member = models.ForeignKey(Member, sf_read_only=models.NOT_UPDATEABLE, \
            on_delete=models.PROTECT, db_column='npe5__Contact__c')

    startdate = models.DateField(db_column='npe5__StartDate__c', \
            verbose_name='Start Date', blank=True, null=True)

    enddate = models.DateField(db_column='npe5__EndDate__c', \
            verbose_name='End Date', blank=True, null=True)

    status = models.CharField(db_column='npe5__Status__c', max_length=255, \
            verbose_name='Status', choices=[('Current', 'Current'), \
            ('Former', 'Former')], blank=True)

    is_primary = models.BooleanField(db_column='Primary_Group__c', \
            verbose_name='Primary Group')

    is_deleted = models.BooleanField(db_column='IsDeleted', \
            verbose_name='Deleted', sf_read_only=models.READ_ONLY)

    lastmodifieddate = models.DateTimeField(db_column='LastModifiedDate', \
            verbose_name='Last Modified Date', sf_read_only=models.READ_ONLY)

    class Meta(models.SalesforceModel.Meta):
        db_table = 'npe5__Affiliation__c'
        verbose_name = 'Affiliation'
        verbose_name_plural = 'Affilitions'
        # keyPrefix = 'a0C'
        managed = False


# Date in which SalesForce data models was last synced with taikonetwork db.
class SyncInfo(django.db.models.Model):
    model_type = django.db.models.CharField(max_length=32)
    lastupdateddate = django.db.models.DateTimeField(auto_now=True)

