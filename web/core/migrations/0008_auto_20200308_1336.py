# Generated by Django 3.0.2 on 2020-03-08 13:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_workspace_trial_end'),
    ]

    operations = [
        migrations.AddField(
            model_name='slackuser',
            name='is_installer',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='slackuser',
            name='slack_email',
            field=models.EmailField(max_length=254, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='slackuser',
            name='slack_id',
            field=models.CharField(max_length=16),
        ),
    ]
