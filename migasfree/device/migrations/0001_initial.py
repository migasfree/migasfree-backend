import django.db.models.deletion
from django.db import migrations, models

import migasfree.core.models.migas_link


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Capability',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='name')),
            ],
            options={
                'verbose_name': 'Capability',
                'verbose_name_plural': 'Capabilities',
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.CreateModel(
            name='Connection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                (
                    'fields',
                    models.CharField(
                        blank=True,
                        help_text='Fields separated by comma',
                        max_length=100,
                        null=True,
                        verbose_name='fields',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Connection',
                'verbose_name_plural': 'Connections',
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.CreateModel(
            name='Manufacturer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='name')),
            ],
            options={
                'verbose_name': 'Manufacturer',
                'verbose_name_plural': 'Manufacturers',
                'ordering': ['name'],
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.CreateModel(
            name='Type',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='name')),
            ],
            options={
                'verbose_name': 'Type',
                'verbose_name_plural': 'Types',
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.CreateModel(
            name='Model',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=50, null=True, verbose_name='name')),
                ('connections', models.ManyToManyField(blank=True, to='device.Connection', verbose_name='connections')),
                (
                    'device_type',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='device.type', verbose_name='type'
                    ),
                ),
                (
                    'manufacturer',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='device.manufacturer',
                        verbose_name='manufacturer',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Model',
                'verbose_name_plural': 'Models',
                'ordering': ['manufacturer', 'name'],
                'unique_together': {('device_type', 'manufacturer', 'name')},
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='name')),
                ('data', models.TextField(default='{}', null=True, verbose_name='data')),
                (
                    'available_for_attributes',
                    models.ManyToManyField(blank=True, to='core.Attribute', verbose_name='available for attributes'),
                ),
                (
                    'connection',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='device.connection', verbose_name='connection'
                    ),
                ),
                (
                    'model',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='device.model', verbose_name='model'
                    ),
                ),
            ],
            options={
                'verbose_name': 'Device',
                'verbose_name_plural': 'Devices',
                'unique_together': {('connection', 'name')},
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.AddField(
            model_name='connection',
            name='device_type',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to='device.type', verbose_name='device type'
            ),
        ),
        migrations.CreateModel(
            name='Logical',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'alternative_capability_name',
                    models.CharField(blank=True, max_length=50, null=True, verbose_name='alternative capability name'),
                ),
                (
                    'attributes',
                    models.ManyToManyField(
                        blank=True, help_text='Assigned Attributes', to='core.Attribute', verbose_name='attributes'
                    ),
                ),
                (
                    'capability',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='device.capability', verbose_name='capability'
                    ),
                ),
                (
                    'device',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='device.device', verbose_name='device'
                    ),
                ),
            ],
            options={
                'verbose_name': 'Logical Device',
                'verbose_name_plural': 'Logical Devices',
                'ordering': [
                    'device__model__manufacturer__name',
                    'device__model__name',
                    'alternative_capability_name',
                    'capability__name',
                    'device__name',
                ],
                'unique_together': {('device', 'capability')},
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.CreateModel(
            name='Driver',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=100, null=True, verbose_name='name')),
                ('packages_to_install', models.TextField(blank=True, null=True, verbose_name='packages to install')),
                (
                    'capability',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='device.capability', verbose_name='capability'
                    ),
                ),
                (
                    'model',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='drivers',
                        to='device.model',
                        verbose_name='model',
                    ),
                ),
                (
                    'project',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='core.project', verbose_name='project'
                    ),
                ),
            ],
            options={
                'verbose_name': 'Driver',
                'verbose_name_plural': 'Drivers',
                'ordering': ['model', 'name'],
                'unique_together': {('model', 'project', 'capability')},
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.AlterUniqueTogether(
            name='connection',
            unique_together={('device_type', 'name')},
        ),
    ]
