import random
import string

from django.db import migrations, models
from django.db.migrations.operations import RunSQL

LEN = 15
CHARACTERS = string.ascii_letters + string.digits + string.punctuation


def get_default_value(apps, schema_editor):
    Model = apps.get_model('core', 'Singularity')
    for obj in Model.objects.all():
        obj.name = ''.join(random.choice(CHARACTERS) for _ in range(LEN))
        obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_singularity'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='singularity',
            options={'ordering': ['property_att__name', '-priority'], 'verbose_name': 'Singularity', 'verbose_name_plural': 'Singularities'},
        ),
        migrations.AddField(
            model_name='singularity',
            name='name',
            field=models.CharField(max_length=50, null=True, verbose_name='name'),
        ),
        RunSQL(migrations.RunSQL.noop, reverse_sql=migrations.RunSQL.noop),
        migrations.RunPython(get_default_value),
        migrations.AlterField(
            model_name='singularity',
            name='name',
            field=models.CharField(max_length=50, unique=True, verbose_name='name', default=None),
        ),
        migrations.AlterUniqueTogether(
            name='singularity',
            unique_together={('name', 'property_att', 'priority')},
        ),
    ]
