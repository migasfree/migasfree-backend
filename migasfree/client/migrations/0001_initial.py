# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2015-12-11 17:02
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0001_initial'),
        ('device', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Computer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.CharField(blank=True, default=b'', max_length=36, null=True, unique=True, verbose_name='uuid')),
                ('status', models.CharField(choices=[(b'intended', 'Intended'), (b'reserved', 'Reserved'), (b'unknown', 'Unknown'), (b'in repair', 'In repair'), (b'available', 'Available'), (b'unsubscribed', 'Unsubscribed')], default=b'intended', max_length=20, verbose_name='status')),
                ('name', models.CharField(blank=True, max_length=50, null=True, verbose_name='name')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='ip address')),
                ('software_history', models.TextField(blank=True, default=b'', null=True, verbose_name='software history')),
                ('logical_devices_assigned', models.ManyToManyField(blank=True, related_name='logical_devices_assigned', to='device.Logical', verbose_name='logical devices assigned')),
                ('logical_devices_installed', models.ManyToManyField(blank=True, editable=False, related_name='logical_devices_installed', to='device.Logical', verbose_name='logical devices installed')),
                ('last_hardware_capture', models.DateTimeField(blank=True, null=True, verbose_name='last hardware capture')),
                ('sync_start_date', models.DateTimeField(null=True, verbose_name='sync start date')),
                ('sync_end_date', models.DateTimeField(null=True, verbose_name='sync end date')),
                ('cpu', models.CharField(blank=True, max_length=50, null=True, verbose_name='CPU')),
                ('disks', models.SmallIntegerField(blank=True, null=True, verbose_name='disks')),
                ('mac_address', models.CharField(blank=True, max_length=60, null=True, verbose_name='MAC address')),
                ('machine', models.CharField(choices=[(b'P', 'Physical'), (b'V', 'Virtual')], default=b'P', max_length=1, verbose_name='machine')),
                ('product', models.CharField(blank=True, max_length=80, null=True, verbose_name='product')),
                ('ram', models.BigIntegerField(blank=True, null=True, verbose_name='RAM')),
                ('storage', models.BigIntegerField(blank=True, null=True, verbose_name='storage')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Project', verbose_name='project')),
            ],
            options={
                'verbose_name': 'Computer',
                'verbose_name_plural': 'Computers',
            },
        ),
        migrations.CreateModel(
            name='Error',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('checked', models.BooleanField(default=False, verbose_name='checked')),
                ('computer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client.Computer', verbose_name='computer')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Project', verbose_name='project')),
            ],
            options={
                'verbose_name': 'Error',
                'verbose_name_plural': 'Errors',
            },
        ),
        migrations.CreateModel(
            name='Fault',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('result', models.TextField(blank=True, null=True, verbose_name='result')),
                ('checked', models.BooleanField(default=False, verbose_name='checked')),
                ('computer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client.Computer', verbose_name='computer')),
            ],
            options={
                'verbose_name': 'Fault',
                'verbose_name_plural': 'Faults',
            },
        ),
        migrations.CreateModel(
            name='FaultDefinition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('enabled', models.BooleanField(default=True, verbose_name='enabled')),
                ('language', models.CharField(choices=[(b'python', b'python'), (b'bash', b'bash'), (b'perl', b'perl'), (b'php', b'php'), (b'ruby', b'ruby'), (b'cmd', b'cmd')], default=(b'python', b'python'), max_length=20, verbose_name='programming language')),
                ('code', models.TextField(blank=True, verbose_name='code')),
                ('excluded_attributes', models.ManyToManyField(blank=True, related_name='ExcludeAttributeFaultDefinition', to='core.Attribute', verbose_name='excluded')),
                ('included_attributes', models.ManyToManyField(blank=True, to='core.Attribute', verbose_name='included')),
            ],
            options={
                'verbose_name': 'Fault Definition',
                'verbose_name_plural': 'Fault Definitions',
            },
        ),
        migrations.CreateModel(
            name='Migration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('computer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client.Computer', verbose_name='computer')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Project', verbose_name='project')),
            ],
            options={
                'verbose_name': 'Migration',
                'verbose_name_plural': 'Migrations',
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('message', models.TextField(verbose_name='message')),
                ('checked', models.BooleanField(default=False, verbose_name='checked')),
            ],
            options={
                'verbose_name': 'Notification',
                'verbose_name_plural': 'Notifications',
            },
        ),
        migrations.CreateModel(
            name='Package',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fullname', models.CharField(max_length=140, unique=True, verbose_name='fullname')),
                ('name', models.CharField(blank=True, max_length=100, verbose_name='name')),
                ('version', models.CharField(max_length=60, verbose_name='version')),
                ('architecture', models.CharField(max_length=10, verbose_name='architecture')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='core.Project', verbose_name='project')),
            ],
            options={
                'verbose_name': 'Package',
                'verbose_name_plural': 'Packages',
            },
        ),
        migrations.CreateModel(
            name='StatusLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[(b'intended', 'Intended'), (b'reserved', 'Reserved'), (b'unknown', 'Unknown'), (b'in repair', 'In repair'), (b'available', 'Available'), (b'unsubscribed', 'Unsubscribed')], default=b'intended', max_length=20, verbose_name='status')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='date')),
                ('computer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client.Computer', verbose_name='computer')),
            ],
            options={
                'verbose_name': 'Status Log',
                'verbose_name_plural': 'Status Logs',
            },
        ),
        migrations.CreateModel(
            name='Synchronization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('start_date', models.DateTimeField(blank=True, null=True, verbose_name='start date connection')),
                ('consumer', models.CharField(max_length=50, null=True, verbose_name='consumer')),
                ('pms_status_ok', models.BooleanField(default=False, help_text='indicates the status of transactions with PMS', verbose_name='PMS status OK')),
                ('computer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client.Computer', verbose_name='computer')),
                ('project', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Project', verbose_name='project')),
            ],
            options={
                'verbose_name': 'Synchronization',
                'verbose_name_plural': 'Synchronizations',
            },
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
            },
        ),
        migrations.AlterUniqueTogether(
            name='user',
            unique_together=set([('name', 'fullname')]),
        ),
        migrations.AddField(
            model_name='synchronization',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client.User', verbose_name='user'),
        ),
        migrations.AddField(
            model_name='faultdefinition',
            name='users',
            field=models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL, verbose_name='users'),
        ),
        migrations.AddField(
            model_name='fault',
            name='fault_definition',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client.FaultDefinition', verbose_name='fault definition'),
        ),
        migrations.AddField(
            model_name='fault',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Project', verbose_name='project'),
        ),
        migrations.AddField(
            model_name='computer',
            name='software_inventory',
            field=models.ManyToManyField(blank=True, to='client.Package', verbose_name='software inventory'),
        ),
        migrations.AddField(
            model_name='computer',
            name='sync_attributes',
            field=models.ManyToManyField(blank=True, help_text='attributes sent', to='core.Attribute', verbose_name='sync attributes'),
        ),
        migrations.AddField(
            model_name='computer',
            name='sync_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='client.User', verbose_name='sync user'),
        ),
        migrations.AddField(
            model_name='computer',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='tags', to='core.ServerAttribute', verbose_name='tags'),
        ),
        migrations.AlterUniqueTogether(
            name='package',
            unique_together=set([('fullname', 'project')]),
        ),
    ]
