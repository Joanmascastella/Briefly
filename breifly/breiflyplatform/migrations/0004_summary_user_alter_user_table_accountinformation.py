# Generated by Django 5.1.4 on 2025-01-17 01:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('breiflyplatform', '0003_alter_user_options_summary_user_delete_userauthmap'),
    ]

    operations = [
        migrations.AddField(
            model_name='summary',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='summaries', to='breiflyplatform.user'),
        ),
        migrations.AlterModelTable(
            name='user',
            table='auth.users',
        ),
        migrations.CreateModel(
            name='AccountInformation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField()),
                ('full_name', models.CharField(max_length=255)),
                ('position', models.CharField(max_length=255)),
                ('company', models.CharField(max_length=255)),
                ('report_email', models.CharField(max_length=255)),
                ('phonenr', models.CharField(blank=True, max_length=20, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='account_information', to='breiflyplatform.user')),
            ],
            options={
                'db_table': 'account_information',
            },
        ),
    ]
