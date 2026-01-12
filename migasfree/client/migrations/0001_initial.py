import django.db.models.deletion
from django.db import migrations, models

import migasfree.core.models.migas_link


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('core', '0001_initial'),
        ('device', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Computer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'uuid',
                    models.CharField(
                        blank=True, default='', max_length=36, null=True, unique=True, verbose_name='uuid'
                    ),
                ),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('intended', 'Intended'),
                            ('reserved', 'Reserved'),
                            ('unknown', 'Unknown'),
                            ('in repair', 'In repair'),
                            ('available', 'Available'),
                            ('unsubscribed', 'Unsubscribed'),
                        ],
                        default='intended',
                        max_length=20,
                        verbose_name='status',
                    ),
                ),
                ('name', models.CharField(blank=True, max_length=50, null=True, verbose_name='name')),
                (
                    'fqdn',
                    models.CharField(blank=True, max_length=255, null=True, verbose_name='full qualified domain name'),
                ),
                (
                    'created_at',
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text='Date of entry into the migasfree system',
                        verbose_name='entry date',
                    ),
                ),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='ip address')),
                (
                    'forwarded_ip_address',
                    models.GenericIPAddressField(blank=True, null=True, verbose_name='forwarded ip address'),
                ),
                (
                    'last_hardware_capture',
                    models.DateTimeField(blank=True, null=True, verbose_name='last hardware capture'),
                ),
                ('sync_start_date', models.DateTimeField(null=True, verbose_name='sync start date')),
                ('sync_end_date', models.DateTimeField(null=True, verbose_name='sync end date')),
                ('product', models.CharField(blank=True, max_length=80, null=True, verbose_name='product')),
                (
                    'machine',
                    models.CharField(
                        choices=[('P', 'Physical'), ('V', 'Virtual')], default='P', max_length=1, verbose_name='machine'
                    ),
                ),
                ('cpu', models.CharField(blank=True, max_length=50, null=True, verbose_name='CPU')),
                ('ram', models.BigIntegerField(blank=True, null=True, verbose_name='RAM')),
                ('storage', models.BigIntegerField(blank=True, null=True, verbose_name='storage')),
                ('disks', models.SmallIntegerField(blank=True, null=True, verbose_name='disks')),
                ('mac_address', models.CharField(blank=True, max_length=60, null=True, verbose_name='MAC address')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='comment')),
                (
                    'default_logical_device',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to='device.logical',
                        verbose_name='default logical device',
                    ),
                ),
                (
                    'project',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='core.project', verbose_name='project'
                    ),
                ),
                (
                    'sync_attributes',
                    models.ManyToManyField(
                        blank=True, help_text='attributes sent', to='core.Attribute', verbose_name='sync attributes'
                    ),
                ),
            ],
            options={
                'verbose_name': 'Computer',
                'verbose_name_plural': 'Computers',
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='date')),
                ('message', models.TextField(verbose_name='message')),
                ('checked', models.BooleanField(default=False, verbose_name='checked')),
            ],
            options={
                'verbose_name': 'Notification',
                'verbose_name_plural': 'Notifications',
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('fullname', models.CharField(blank=True, max_length=100, verbose_name='fullname')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
                'unique_together': {('name', 'fullname')},
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.CreateModel(
            name='Synchronization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='date')),
                ('start_date', models.DateTimeField(blank=True, null=True, verbose_name='start date connection')),
                ('consumer', models.CharField(max_length=50, null=True, verbose_name='consumer')),
                (
                    'pms_status_ok',
                    models.BooleanField(
                        default=False,
                        help_text='indicates the status of transactions with PMS',
                        verbose_name='PMS status OK',
                    ),
                ),
                (
                    'computer',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='client.computer', verbose_name='computer'
                    ),
                ),
                (
                    'project',
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to='core.project',
                        verbose_name='project',
                    ),
                ),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='client.user', verbose_name='user'
                    ),
                ),
            ],
            options={
                'verbose_name': 'Synchronization',
                'verbose_name_plural': 'Synchronizations',
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.CreateModel(
            name='StatusLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='date')),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('intended', 'Intended'),
                            ('reserved', 'Reserved'),
                            ('unknown', 'Unknown'),
                            ('in repair', 'In repair'),
                            ('available', 'Available'),
                            ('unsubscribed', 'Unsubscribed'),
                        ],
                        default='intended',
                        max_length=20,
                        verbose_name='status',
                    ),
                ),
                (
                    'computer',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='client.computer', verbose_name='computer'
                    ),
                ),
            ],
            options={
                'verbose_name': 'Status Log',
                'verbose_name_plural': 'Status Logs',
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.CreateModel(
            name='PackageHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('install_date', models.DateTimeField(auto_now_add=True, null=True, verbose_name='install date')),
                ('uninstall_date', models.DateTimeField(null=True, verbose_name='uninstall date')),
                (
                    'computer',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='client.computer', verbose_name='computer'
                    ),
                ),
                (
                    'package',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='core.package', verbose_name='package'
                    ),
                ),
            ],
            options={
                'verbose_name': 'Package History',
                'verbose_name_plural': 'Packages History',
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.CreateModel(
            name='Migration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='date')),
                (
                    'computer',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='client.computer', verbose_name='computer'
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
                'verbose_name': 'Migration',
                'verbose_name_plural': 'Migrations',
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.CreateModel(
            name='FaultDefinition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('enabled', models.BooleanField(default=True, verbose_name='enabled')),
                (
                    'language',
                    models.IntegerField(
                        choices=[
                            (0, 'bash'),
                            (1, 'python'),
                            (2, 'perl'),
                            (3, 'php'),
                            (4, 'ruby'),
                            (5, 'cmd'),
                            (6, 'powershell'),
                        ],
                        default=0,
                        verbose_name='programming language',
                    ),
                ),
                ('code', models.TextField(blank=True, verbose_name='code')),
                (
                    'excluded_attributes',
                    models.ManyToManyField(
                        blank=True,
                        related_name='faultdefinition_excluded',
                        to='core.Attribute',
                        verbose_name='excluded attributes',
                    ),
                ),
                (
                    'included_attributes',
                    models.ManyToManyField(
                        blank=True,
                        related_name='faultdefinition_included',
                        to='core.Attribute',
                        verbose_name='included attributes',
                    ),
                ),
                (
                    'users',
                    models.ManyToManyField(
                        blank=True, related_name='faultdefinition_users', to='core.UserProfile', verbose_name='users'
                    ),
                ),
            ],
            options={
                'verbose_name': 'Fault Definition',
                'verbose_name_plural': 'Fault Definitions',
                'ordering': ['name'],
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.CreateModel(
            name='Fault',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='date')),
                ('result', models.TextField(blank=True, null=True, verbose_name='result')),
                ('checked', models.BooleanField(default=False, verbose_name='checked')),
                (
                    'computer',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='client.computer', verbose_name='computer'
                    ),
                ),
                (
                    'fault_definition',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='client.faultdefinition',
                        verbose_name='fault definition',
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
                'verbose_name': 'Fault',
                'verbose_name_plural': 'Faults',
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.CreateModel(
            name='Error',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='date')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('checked', models.BooleanField(default=False, verbose_name='checked')),
                (
                    'computer',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='client.computer', verbose_name='computer'
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
                'verbose_name': 'Error',
                'verbose_name_plural': 'Errors',
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.AddField(
            model_name='computer',
            name='sync_user',
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.CASCADE, to='client.user', verbose_name='sync user'
            ),
        ),
        migrations.AddField(
            model_name='computer',
            name='tags',
            field=models.ManyToManyField(
                blank=True, related_name='tags', to='core.ServerAttribute', verbose_name='tags'
            ),
        ),
        migrations.AddIndex(
            model_name='synchronization',
            index=models.Index(fields=['created_at'], name='client_sync_created_326a8e_idx'),
        ),
        migrations.AddIndex(
            model_name='computer',
            index=models.Index(fields=['name'], name='client_comp_name_e8d405_idx'),
        ),
    ]
