# Generated by Django 3.0.2 on 2020-04-29 22:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_auto_20200413_1709'),
    ]

    operations = [
        migrations.AlterField(
            model_name='slackuser',
            name='slack_email',
            field=models.EmailField(max_length=254, null=True),
        ),
    ]