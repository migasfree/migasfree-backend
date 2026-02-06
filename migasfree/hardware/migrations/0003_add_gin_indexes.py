import django.contrib.postgres.indexes
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('client', '0004_add_gin_indexes'),
        ('hardware', '0002_alter_comments'),
    ]

    operations = [
        migrations.AlterModelTableComment(
            name='node',
            table_comment='hierarchical structure of the hardware in the system (it details the individual components and their relationships, indicating how they are organized and connected within the overall architecture of the system)',
        ),
        migrations.AddIndex(
            model_name='node',
            index=django.contrib.postgres.indexes.GinIndex(
                fields=['name'], name='node_name_trgm_idx', opclasses=['gin_trgm_ops']
            ),
        ),
        migrations.AddIndex(
            model_name='node',
            index=django.contrib.postgres.indexes.GinIndex(
                fields=['serial'], name='node_serial_trgm_idx', opclasses=['gin_trgm_ops']
            ),
        ),
    ]
