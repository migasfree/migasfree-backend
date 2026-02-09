import django.contrib.postgres.indexes
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('app_catalog', '0002_alter_comments'),
        ('device', '0004_install_trigram_extension'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='application',
            index=django.contrib.postgres.indexes.GinIndex(
                fields=['name'], name='app_name_trgm_idx', opclasses=['gin_trgm_ops']
            ),
        ),
        migrations.AddIndex(
            model_name='application',
            index=django.contrib.postgres.indexes.GinIndex(
                fields=['description'], name='app_desc_trgm_idx', opclasses=['gin_trgm_ops']
            ),
        ),
    ]
