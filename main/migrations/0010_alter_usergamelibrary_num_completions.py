# Generated by Django 5.0.7 on 2024-09-04 10:44

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0009_usergamelibrary_hours_played_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usergamelibrary',
            name='num_completions',
            field=models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
    ]
