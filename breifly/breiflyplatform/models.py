from django.db import models
from django.utils.timezone import now

# Supabase Users Table Model
class User(models.Model):
    id = models.UUIDField(primary_key=True)  # Supabase's user ID
    display_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(unique=True)
    provider = models.CharField(max_length=50, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    provider_type = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField()
    last_sign_in_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'auth.users'  # Exact table name in Supabase
        managed = False  # Prevent Django from managing this table


# Settings Model
class Setting(models.Model):
    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='settings')
    date_range = models.CharField(max_length=50)
    email_reports = models.BooleanField(default=False)
    report_time = models.TimeField(null=True, blank=True)
    timezone = models.CharField(max_length=50, null=True, blank=True)
    language = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'settings'


# Search Settings Model
class SearchSetting(models.Model):
    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='search_settings')
    keywords = models.TextField()
    publishers = models.TextField()
    frequency = models.CharField(max_length=50)
    search_description = models.TextField()

    class Meta:
        db_table = 'search_settings'


# Previous Searches Model
class PreviousSearch(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='previous_searches')
    keyword = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    csv_file_path = models.CharField(max_length=255)

    class Meta:
        db_table = 'previous_searches'


# Summaries Model
class Summary(models.Model):
    user = models.ForeignKey(
        'User', on_delete=models.CASCADE, related_name='summaries', null=True, blank=True
    )
    csv_file_path = models.CharField(max_length=255)
    article_title = models.CharField(max_length=255)
    publisher = models.CharField(max_length=255)
    url = models.URLField()

    class Meta:
        db_table = 'summaries'

# Account Information Model
class AccountInformation(models.Model):
    user = models.ForeignKey(
        'User', on_delete=models.CASCADE, related_name='account_information'
    )
    created_at = models.DateTimeField(default=now)
    full_name = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    report_email = models.CharField(max_length=255)
    phonenr = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        db_table = 'account_information'
