from django.db import models
from django.utils.timezone import now

# Supabase Users Table Model
class User(models.Model):
    id = models.UUIDField(primary_key=True)  # Supabase's user ID
    email = models.EmailField(unique=True)

    class Meta:
        db_table = '"auth"."users"'
        managed = False  # Prevent Django from managing this table


# Roles Model
class Role(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'roles'
        managed = False


# User Roles Model
class UserRole(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, db_column='user_id', related_name='user_roles'
    )
    role = models.ForeignKey(
        Role, on_delete=models.CASCADE, db_column='role_id', related_name='user_roles'
    )
    assigned_at = models.DateTimeField(default=now)

    class Meta:
        db_table = 'user_roles'
        managed = False


# Settings Model
class Setting(models.Model):
    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='settings')
    email_reports = models.BooleanField(default=False)
    timezone = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'settings'


# Search Settings Model
class SearchSetting(models.Model):
    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='search_settings')
    keywords = models.TextField()
    publishers = models.TextField()
    frequency = models.CharField(max_length=50)
    search_description = models.TextField()
    type_of_search = models.TextField(default='')

    class Meta:
        db_table = 'search_settings'

# Schedulded Search Model
class ScheduledSearch(models.Model):
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='scheduled_searches'
    )
    search_settings = models.ForeignKey(
        'SearchSetting',
        on_delete=models.CASCADE,
        related_name='scheduled_searches',
        db_column='search_settings_id'
    )
    date_of_execution = models.DateField()
    time_of_execution = models.TimeField()
    created_at = models.DateTimeField(default=now)

    class Meta:
        db_table = 'scheduled_search'


# Previous Searches Model
class PreviousSearch(models.Model):
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='previous_searches'
    )
    search_setting = models.ForeignKey(
        'SearchSetting',
        on_delete=models.CASCADE,
        related_name='previous_searches',
        null=True,
        blank=True,
        db_column='search_settings_id'
    )
    keyword = models.CharField(max_length=255)
    search_description = models.CharField(max_length=255, default="a")
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
    target_audience = models.CharField(max_length=255, default='')
    industry = models.CharField(max_length=255, default='')
    content_sentiment = models.CharField(max_length=255, default='')
    company_brief = models.CharField(max_length=255, default='')
    recent_ventures = models.CharField(max_length=255, default='')
    account_version = models.CharField(max_length=35, default='')

    class Meta:
        db_table = 'account_information'
