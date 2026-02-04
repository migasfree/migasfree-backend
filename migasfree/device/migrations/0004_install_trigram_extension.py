from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('device', '0003_alter_model_name'),
    ]

    operations = [
        TrigramExtension(),
    ]
