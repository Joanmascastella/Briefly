# Generated by Django 5.1.4 on 2025-01-16 08:19

import django.db.models.deletion
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('breiflyplatform', '0002_previoussearch_searchsetting_setting_summary_user_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'managed': False},  # Tells Django not to manage the User table schema
        ),
        migrations.DeleteModel(
            name='UserAuthMap',  # Deletes the obsolete UserAuthMap model
        ),
    ]