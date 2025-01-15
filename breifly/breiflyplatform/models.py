from django.db import models

# User Model
class User(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    company = models.CharField(max_length=255, null=True, blank=True)
    password = models.CharField(max_length=255)
    provider = models.CharField(max_length=50)
    last_logged_in = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users'

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
    publishers = models.TextField()
    frequency = models.CharField(max_length=50)

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
    csv_file_path = models.CharField(max_length=255)
    article_title = models.CharField(max_length=255)
    publisher = models.CharField(max_length=255)
    url = models.URLField()

    class Meta:
        db_table = 'summaries'

# User Auth Map Model
class UserAuthMap(models.Model):
    auth_uid = models.CharField(max_length=255, unique=True)
    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='auth_map')

    class Meta:
        db_table = 'user_auth_map'