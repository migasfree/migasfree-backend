import django.contrib.postgres.indexes
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('device', '0004_install_trigram_extension'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='manufacturer',
            index=django.contrib.postgres.indexes.GinIndex(
                fields=['name'],
                name='manufacturer_name_gin',
                opclasses=['gin_trgm_ops'],
            ),
        ),
        migrations.AddIndex(
            model_name='model',
            index=django.contrib.postgres.indexes.GinIndex(
                fields=['name'], name='model_name_gin', opclasses=['gin_trgm_ops']
            ),
        ),
    ]
