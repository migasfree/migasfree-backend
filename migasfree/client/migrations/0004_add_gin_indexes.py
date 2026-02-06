import django.contrib.postgres.indexes
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('client', '0003_add_synchronization_to_errors_and_faults'),
        ('device', '0006_device_device_name_trgm_idx_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='computer',
            index=django.contrib.postgres.indexes.GinIndex(
                fields=['mac_address'], name='computer_mac_trgm_idx', opclasses=['gin_trgm_ops']
            ),
        ),
    ]
