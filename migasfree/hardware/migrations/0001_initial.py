import django.db.models.deletion
from django.db import migrations, models

import migasfree.core.models.migas_link


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('client', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Node',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.IntegerField(verbose_name='level')),
                ('width', models.BigIntegerField(null=True, verbose_name='width')),
                ('name', models.TextField(blank=True, verbose_name='id')),
                ('class_name', models.TextField(blank=True, verbose_name='class')),
                ('enabled', models.BooleanField(default=False, verbose_name='enabled')),
                ('claimed', models.BooleanField(default=False, verbose_name='claimed')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('vendor', models.TextField(blank=True, null=True, verbose_name='vendor')),
                ('product', models.TextField(blank=True, null=True, verbose_name='product')),
                ('version', models.TextField(blank=True, null=True, verbose_name='version')),
                ('serial', models.TextField(blank=True, null=True, verbose_name='serial')),
                ('bus_info', models.TextField(blank=True, null=True, verbose_name='bus info')),
                ('physid', models.TextField(blank=True, null=True, verbose_name='physid')),
                ('slot', models.TextField(blank=True, null=True, verbose_name='slot')),
                ('size', models.BigIntegerField(null=True, verbose_name='size')),
                ('capacity', models.BigIntegerField(null=True, verbose_name='capacity')),
                ('clock', models.BigIntegerField(null=True, verbose_name='clock')),
                ('dev', models.TextField(blank=True, null=True, verbose_name='dev')),
                (
                    'computer',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='client.computer', verbose_name='computer'
                    ),
                ),
                (
                    'parent',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='child',
                        to='hardware.node',
                        verbose_name='parent',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Hardware Node',
                'verbose_name_plural': 'Hardware Nodes',
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.CreateModel(
            name='LogicalName',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(blank=True, verbose_name='name')),
                (
                    'node',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='hardware.node', verbose_name='hardware node'
                    ),
                ),
            ],
            options={
                'verbose_name': 'Hardware Logical Name',
                'verbose_name_plural': 'Hardware Logical Names',
            },
        ),
        migrations.CreateModel(
            name='Configuration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(blank=True, verbose_name='name')),
                ('value', models.TextField(blank=True, null=True, verbose_name='value')),
                (
                    'node',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='hardware.node', verbose_name='hardware node'
                    ),
                ),
            ],
            options={
                'verbose_name': 'Hardware Configuration',
                'verbose_name_plural': 'Hardware Configurations',
                'unique_together': {('name', 'node')},
            },
        ),
        migrations.CreateModel(
            name='Capability',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(blank=True, verbose_name='name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                (
                    'node',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='hardware.node', verbose_name='hardware node'
                    ),
                ),
            ],
            options={
                'verbose_name': 'Hardware Capability',
                'verbose_name_plural': 'Hardware Capabilities',
                'unique_together': {('name', 'node')},
            },
        ),
    ]
