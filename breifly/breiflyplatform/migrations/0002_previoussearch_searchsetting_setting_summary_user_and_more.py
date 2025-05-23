# Generated by Django 5.1.4 on 2025-01-15 02:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('breiflyplatform', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PreviousSearch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('keyword', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('csv_file_path', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'previous_searches',
            },
        ),
        migrations.CreateModel(
            name='SearchSetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('publishers', models.TextField()),
                ('frequency', models.CharField(max_length=50)),
            ],
            options={
                'db_table': 'search_settings',
            },
        ),
        migrations.CreateModel(
            name='Setting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_range', models.CharField(max_length=50)),
                ('email_reports', models.BooleanField(default=False)),
                ('report_time', models.TimeField(blank=True, null=True)),
                ('timezone', models.CharField(blank=True, max_length=50, null=True)),
                ('language', models.CharField(blank=True, max_length=50, null=True)),
            ],
            options={
                'db_table': 'settings',
            },
        ),
        migrations.CreateModel(
            name='Summary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('csv_file_path', models.CharField(max_length=255)),
                ('article_title', models.CharField(max_length=255)),
                ('publisher', models.CharField(max_length=255)),
                ('url', models.URLField()),
            ],
            options={
                'db_table': 'summaries',
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('company', models.CharField(blank=True, max_length=255, null=True)),
                ('password', models.CharField(max_length=255)),
                ('provider', models.CharField(max_length=50)),
                ('last_logged_in', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'users',
            },
        ),
        migrations.CreateModel(
            name='UserAuthMap',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('auth_uid', models.CharField(max_length=255, unique=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='auth_map', to='breiflyplatform.user')),
            ],
            options={
                'db_table': 'user_auth_map',
            },
        ),
        migrations.DeleteModel(
            name='TestModel',
        ),
        migrations.AddField(
            model_name='setting',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='settings', to='breiflyplatform.user'),
        ),
        migrations.AddField(
            model_name='searchsetting',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='search_settings', to='breiflyplatform.user'),
        ),
        migrations.AddField(
            model_name='previoussearch',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='previous_searches', to='breiflyplatform.user'),
        ),
    ]
