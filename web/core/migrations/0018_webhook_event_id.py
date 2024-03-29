# Generated by Django 3.0.2 on 2020-05-06 13:03
from calendly import Calendly
from django.db import migrations, models


def create_event_destination(apps, schema_editor):
    Webhook = apps.get_model('core', 'Webhook')

    for w in Webhook.objects.all():
        if w.user:
            calendly = Calendly(w.user.calendly_authtoken)
            events = calendly.event_types()
            if 'data' in events:
                active_event_ids = [e['id'] for e in events['data'] if e['attributes']['active']]
                if active_event_ids:
                    w.event_id = active_event_ids[0]
                    for new_hook in active_event_ids[1:]:
                        Webhook.objects.create(user=w.user, calendly_id=w.calendly_id, destination_id=w.destination_id, event_id=new_hook)
                else:
                    print(f'Somethings not right events {events}')
                    w.event_id = ''
                w.save()
            else:
                print(f'Somethings not right for user {w.user}')
        else:
            w.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_auto_20200429_2237'),
    ]

    operations = [
        migrations.AddField(
            model_name='webhook',
            name='event_id',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.RunPython(create_event_destination, migrations.RunPython.noop)
    ]
