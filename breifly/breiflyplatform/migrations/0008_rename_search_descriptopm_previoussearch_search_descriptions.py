# Generated by Django 5.1.4 on 2025-01-17 07:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('breiflyplatform', '0007_previoussearch_search_descriptopm_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='previoussearch',
            old_name='search_descriptopm',
            new_name='search_descriptions',
        ),
    ]
