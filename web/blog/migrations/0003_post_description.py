# Generated by Django 3.0.2 on 2020-06-04 15:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0002_auto_20200604_1301'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='description',
            field=models.CharField(default='', max_length=150, unique=True),
            preserve_default=False,
        ),
    ]