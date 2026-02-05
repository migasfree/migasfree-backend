import django.contrib.postgres.indexes
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0009_alter_deployment_start_date_alter_project_pms'),
        ('device', '0005_manufacturer_manufacturer_name_gin_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='device',
            index=django.contrib.postgres.indexes.GinIndex(
                fields=['name'], name='device_name_trgm_idx', opclasses=['gin_trgm_ops']
            ),
        ),
        migrations.AddIndex(
            model_name='device',
            index=django.contrib.postgres.indexes.GinIndex(
                fields=['data'], name='device_data_trgm_idx', opclasses=['gin_trgm_ops']
            ),
        ),
    ]
