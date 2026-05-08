from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('hardware', '0003_add_gin_indexes'),
    ]

    operations = [
        migrations.AlterModelTableComment(
            name='capability',
            table_comment='features and functionalities supported by the hardware components of the system (each entry describes a specific capability, such as support for certain protocols, standards, or performance metrics)',
        ),
        migrations.AlterModelTableComment(
            name='configuration',
            table_comment='settings and parameters of the hardware components (it outlines how each component is configured, including resource allocation, operational modes, and any specific options that affect performance)',
        ),
        migrations.AlterModelTableComment(
            name='logicalname',
            table_comment='logical identifiers assigned to each hardware component (these names serve as references for easier identification and management of the components within the system, facilitating tasks such as configuration and troubleshooting)',
        ),
    ]
