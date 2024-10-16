from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0002_alter_comments'),
        ('hardware', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelTableComment(
            name='capability',
            table_comment='features and functionalities supported by the hardware components of the system',
        ),
        migrations.AlterModelTableComment(
            name='configuration',
            table_comment='settings and parameters of the hardware components (it outlines how each component',
        ),
        migrations.AlterModelTableComment(
            name='logicalname',
            table_comment='logical identifiers assigned to each hardware component (these names serve as references',
        ),
        migrations.AlterModelTableComment(
            name='node',
            table_comment='hierarchical structure of the hardware in the system (it details the individual components',
        ),
        migrations.AlterField(
            model_name='capability',
            name='description',
            field=models.TextField(blank=True, db_comment='hardware capability description', null=True, verbose_name='description'),
        ),
        migrations.AlterField(
            model_name='capability',
            name='name',
            field=models.TextField(blank=True, db_comment='hardware capability name (lshw field)', verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='capability',
            name='node',
            field=models.ForeignKey(db_comment='related hardware node', on_delete=django.db.models.deletion.CASCADE, to='hardware.node', verbose_name='hardware node'),
        ),
        migrations.AlterField(
            model_name='configuration',
            name='name',
            field=models.TextField(blank=True, db_comment='config field in lshw', verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='configuration',
            name='node',
            field=models.ForeignKey(db_comment='related hardware node', on_delete=django.db.models.deletion.CASCADE, to='hardware.node', verbose_name='hardware node'),
        ),
        migrations.AlterField(
            model_name='configuration',
            name='value',
            field=models.TextField(blank=True, db_comment='hardware configuration value', null=True, verbose_name='value'),
        ),
        migrations.AlterField(
            model_name='logicalname',
            name='name',
            field=models.TextField(blank=True, db_comment='logicalname field in lshw', verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='logicalname',
            name='node',
            field=models.ForeignKey(db_comment='related hardware node', on_delete=django.db.models.deletion.CASCADE, to='hardware.node', verbose_name='hardware node'),
        ),
        migrations.AlterField(
            model_name='node',
            name='bus_info',
            field=models.TextField(blank=True, db_comment='bus info', null=True, verbose_name='bus info'),
        ),
        migrations.AlterField(
            model_name='node',
            name='capacity',
            field=models.BigIntegerField(db_comment='hardware node capacity', null=True, verbose_name='capacity'),
        ),
        migrations.AlterField(
            model_name='node',
            name='claimed',
            field=models.BooleanField(db_comment='indicates whether the hardware node is claimed', default=False, verbose_name='claimed'),
        ),
        migrations.AlterField(
            model_name='node',
            name='class_name',
            field=models.TextField(blank=True, db_comment='class field in lshw', verbose_name='class'),
        ),
        migrations.AlterField(
            model_name='node',
            name='clock',
            field=models.BigIntegerField(db_comment='hardware node clock speed', null=True, verbose_name='clock'),
        ),
        migrations.AlterField(
            model_name='node',
            name='computer',
            field=models.ForeignKey(db_comment='related computer', on_delete=django.db.models.deletion.CASCADE, to='client.computer', verbose_name='computer'),
        ),
        migrations.AlterField(
            model_name='node',
            name='description',
            field=models.TextField(blank=True, db_comment='hardware node description', null=True, verbose_name='description'),
        ),
        migrations.AlterField(
            model_name='node',
            name='dev',
            field=models.TextField(blank=True, db_comment='hardware node device', null=True, verbose_name='dev'),
        ),
        migrations.AlterField(
            model_name='node',
            name='enabled',
            field=models.BooleanField(db_comment='indicates whether the hardware node is enabled', default=False, verbose_name='enabled'),
        ),
        migrations.AlterField(
            model_name='node',
            name='level',
            field=models.IntegerField(db_comment='level of hierarchy between hardware nodes', verbose_name='level'),
        ),
        migrations.AlterField(
            model_name='node',
            name='name',
            field=models.TextField(blank=True, db_comment='id field in lshw', verbose_name='id'),
        ),
        migrations.AlterField(
            model_name='node',
            name='parent',
            field=models.ForeignKey(blank=True, db_comment='hardware node parent', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='child', to='hardware.node', verbose_name='parent'),
        ),
        migrations.AlterField(
            model_name='node',
            name='physid',
            field=models.TextField(blank=True, db_comment='hardware node physical identifier', null=True, verbose_name='physid'),
        ),
        migrations.AlterField(
            model_name='node',
            name='product',
            field=models.TextField(blank=True, db_comment='hardware node product name', null=True, verbose_name='product'),
        ),
        migrations.AlterField(
            model_name='node',
            name='serial',
            field=models.TextField(blank=True, db_comment='hardware node serial code', null=True, verbose_name='serial'),
        ),
        migrations.AlterField(
            model_name='node',
            name='size',
            field=models.BigIntegerField(db_comment='hardware node size', null=True, verbose_name='size'),
        ),
        migrations.AlterField(
            model_name='node',
            name='slot',
            field=models.TextField(blank=True, db_comment='hardware node slot', null=True, verbose_name='slot'),
        ),
        migrations.AlterField(
            model_name='node',
            name='vendor',
            field=models.TextField(blank=True, db_comment='hardware node vendor', null=True, verbose_name='vendor'),
        ),
        migrations.AlterField(
            model_name='node',
            name='version',
            field=models.TextField(blank=True, db_comment='hardware node version', null=True, verbose_name='version'),
        ),
        migrations.AlterField(
            model_name='node',
            name='width',
            field=models.BigIntegerField(db_comment='hardware node width', null=True, verbose_name='width'),
        ),
    ]
