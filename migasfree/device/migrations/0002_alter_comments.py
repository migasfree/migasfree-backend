import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0005_alter_comments'),
        ('device', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelTableComment(
            name='capability',
            table_comment='device driver default settings',
        ),
        migrations.AlterModelTableComment(
            name='connection',
            table_comment='different ways you can physically connect the device',
        ),
        migrations.AlterModelTableComment(
            name='device',
            table_comment='device inventory',
        ),
        migrations.AlterModelTableComment(
            name='driver',
            table_comment='device drivers',
        ),
        migrations.AlterModelTableComment(
            name='logical',
            table_comment='logical device features',
        ),
        migrations.AlterModelTableComment(
            name='manufacturer',
            table_comment='device manufacturers',
        ),
        migrations.AlterModelTableComment(
            name='model',
            table_comment='device models',
        ),
        migrations.AlterModelTableComment(
            name='type',
            table_comment='device types (printer, scanner, ...)',
        ),
        migrations.AlterField(
            model_name='capability',
            name='name',
            field=models.CharField(
                db_comment='capability name (default device driver configuration)',
                max_length=50,
                unique=True,
                verbose_name='name',
            ),
        ),
        migrations.AlterField(
            model_name='connection',
            name='device_type',
            field=models.ForeignKey(
                db_comment='related device type',
                on_delete=django.db.models.deletion.CASCADE,
                to='device.type',
                verbose_name='device type',
            ),
        ),
        migrations.AlterField(
            model_name='connection',
            name='fields',
            field=models.CharField(
                blank=True,
                db_comment='required fields to configure the connection',
                help_text='Fields separated by comma',
                max_length=100,
                null=True,
                verbose_name='fields',
            ),
        ),
        migrations.AlterField(
            model_name='connection',
            name='name',
            field=models.CharField(
                db_comment='how to physically connect the device', max_length=50, verbose_name='name'
            ),
        ),
        migrations.AlterField(
            model_name='device',
            name='connection',
            field=models.ForeignKey(
                db_comment='related device connection',
                on_delete=django.db.models.deletion.CASCADE,
                to='device.connection',
                verbose_name='connection',
            ),
        ),
        migrations.AlterField(
            model_name='device',
            name='data',
            field=models.TextField(
                db_comment='list of fields and values for device connection',
                default='{}',
                null=True,
                verbose_name='data',
            ),
        ),
        migrations.AlterField(
            model_name='device',
            name='model',
            field=models.ForeignKey(
                db_comment='related device model',
                on_delete=django.db.models.deletion.CASCADE,
                to='device.model',
                verbose_name='model',
            ),
        ),
        migrations.AlterField(
            model_name='device',
            name='name',
            field=models.CharField(
                db_comment='device name (it may be an organization code)',
                max_length=50,
                unique=True,
                verbose_name='name',
            ),
        ),
        migrations.AlterField(
            model_name='driver',
            name='capability',
            field=models.ForeignKey(
                db_comment='related device capability',
                on_delete=django.db.models.deletion.CASCADE,
                to='device.capability',
                verbose_name='capability',
            ),
        ),
        migrations.AlterField(
            model_name='driver',
            name='model',
            field=models.ForeignKey(
                db_comment='related device model',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='drivers',
                to='device.model',
                verbose_name='model',
            ),
        ),
        migrations.AlterField(
            model_name='driver',
            name='name',
            field=models.CharField(
                blank=True, db_comment='driver name or driver file path', max_length=100, null=True, verbose_name='name'
            ),
        ),
        migrations.AlterField(
            model_name='driver',
            name='packages_to_install',
            field=models.TextField(
                blank=True,
                db_comment='required packages for the device driver to work',
                null=True,
                verbose_name='packages to install',
            ),
        ),
        migrations.AlterField(
            model_name='driver',
            name='project',
            field=models.ForeignKey(
                db_comment='related project',
                on_delete=django.db.models.deletion.CASCADE,
                to='core.project',
                verbose_name='project',
            ),
        ),
        migrations.AlterField(
            model_name='logical',
            name='alternative_capability_name',
            field=models.CharField(
                blank=True,
                db_comment='alternative capability name',
                max_length=50,
                null=True,
                verbose_name='alternative capability name',
            ),
        ),
        migrations.AlterField(
            model_name='logical',
            name='capability',
            field=models.ForeignKey(
                db_comment='related device capability',
                on_delete=django.db.models.deletion.CASCADE,
                to='device.capability',
                verbose_name='capability',
            ),
        ),
        migrations.AlterField(
            model_name='logical',
            name='device',
            field=models.ForeignKey(
                db_comment='related device',
                on_delete=django.db.models.deletion.CASCADE,
                to='device.device',
                verbose_name='device',
            ),
        ),
        migrations.AlterField(
            model_name='manufacturer',
            name='name',
            field=models.CharField(
                db_comment='device manufacturer name', max_length=50, unique=True, verbose_name='name'
            ),
        ),
        migrations.AlterField(
            model_name='model',
            name='device_type',
            field=models.ForeignKey(
                db_comment='related device type',
                on_delete=django.db.models.deletion.CASCADE,
                to='device.type',
                verbose_name='type',
            ),
        ),
        migrations.AlterField(
            model_name='model',
            name='manufacturer',
            field=models.ForeignKey(
                db_comment='related device manufacturer',
                on_delete=django.db.models.deletion.CASCADE,
                to='device.manufacturer',
                verbose_name='manufacturer',
            ),
        ),
        migrations.AlterField(
            model_name='model',
            name='name',
            field=models.CharField(
                blank=True, db_comment='device model name', max_length=50, null=True, verbose_name='name'
            ),
        ),
        migrations.AlterField(
            model_name='type',
            name='name',
            field=models.CharField(
                db_comment='device type name (printer, scanner, ...)', max_length=50, unique=True, verbose_name='name'
            ),
        ),
    ]
