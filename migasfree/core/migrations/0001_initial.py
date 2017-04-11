# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import migasfree.core.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Attribute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=250, verbose_name='value')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('longitude', models.FloatField(blank=True, null=True, verbose_name='longitude')),
                ('latitude', models.FloatField(blank=True, null=True, verbose_name='latitude')),
            ],
            options={
                'ordering': ['property_att__prefix', 'value'],
                'verbose_name': 'Attribute',
                'verbose_name_plural': 'Attributes',
            },
        ),
        migrations.CreateModel(
            name='AttributeSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('enabled', models.BooleanField(default=True, verbose_name='enabled')),
                ('longitude', models.FloatField(blank=True, null=True, verbose_name='longitude')),
                ('latitude', models.FloatField(blank=True, null=True, verbose_name='latitude')),
                ('excluded_attributes', models.ManyToManyField(blank=True, related_name='ExcludedAttributesGroup', to='core.Attribute', verbose_name='excluded attributes')),
                ('included_attributes', models.ManyToManyField(blank=True, to='core.Attribute', verbose_name='included attributes')),
            ],
            options={
                'verbose_name': 'Attribute Set',
                'verbose_name_plural': 'Attribute Sets',
            },
        ),
        migrations.CreateModel(
            name='Deployment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enabled', models.BooleanField(default=True, help_text='if you uncheck this field, deployment is disabled for all computers.', verbose_name='enabled')),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('slug', models.SlugField(unique=True, verbose_name='slug')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='comment')),
                ('packages_to_install', models.TextField(blank=True, help_text='Mandatory packages to install each time', null=True, verbose_name='packages to install')),
                ('packages_to_remove', models.TextField(blank=True, help_text='Mandatory packages to remove each time', null=True, verbose_name='packages to remove')),
                ('start_date', models.DateField(default=django.utils.timezone.now, verbose_name='start date')),
                ('default_preincluded_packages', models.TextField(blank=True, null=True, verbose_name='default pre-included packages')),
                ('default_included_packages', models.TextField(blank=True, null=True, verbose_name='default included packages')),
                ('default_excluded_packages', models.TextField(blank=True, null=True, verbose_name='default excluded packages')),
            ],
            options={
                'ordering': ['project__name', 'name'],
                'verbose_name': 'Deployment',
                'verbose_name_plural': 'Deployments',
            },
        ),
        migrations.CreateModel(
            name='Package',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='name')),
            ],
            options={
                'verbose_name': 'Package/Set',
                'verbose_name_plural': 'Packages/Sets',
            },
        ),
        migrations.CreateModel(
            name='Platform',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=50, null=True, unique=True, verbose_name='name')),
            ],
            options={
                'verbose_name': 'Platform',
                'verbose_name_plural': 'Platforms',
            },
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='name')),
                ('slug', models.SlugField(unique=True, verbose_name='slug')),
                ('pms', models.CharField(choices=[(b'apt', b'apt'), (b'yum', b'yum'), (b'zypper', b'zypper')], max_length=50, validators=[migasfree.core.validators.validate_project_pms], verbose_name='package management system')),
                ('architecture', models.CharField(max_length=20, verbose_name='architecture')),
                ('auto_register_computers', models.BooleanField(default=False, help_text='Is not needed a user for register computers in database and get the keys.', verbose_name='auto register computers')),
                ('platform', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Platform', verbose_name='platform')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'Project',
                'verbose_name_plural': 'Projects',
            },
        ),
        migrations.CreateModel(
            name='Property',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prefix', models.CharField(max_length=3, unique=True, verbose_name='prefix')),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('enabled', models.BooleanField(default=True, verbose_name='enabled')),
                ('kind', models.CharField(choices=[(b'N', 'Normal'), (b'-', 'List'), (b'L', 'Added to the left'), (b'R', 'Added to the right')], default=b'N', max_length=1, verbose_name='kind')),
                ('sort', models.CharField(choices=[(b'basic', 'Basic'), (b'client', 'Client'), (b'server', 'Server')], default=b'client', max_length=10, verbose_name='sort')),
                ('language', models.IntegerField(choices=[(0, b'bash'), (1, b'python'), (2, b'perl'), (3, b'php'), (4, b'ruby'), (5, b'cmd')], default=0, verbose_name='programming language')),
                ('code', models.TextField(blank=True, help_text="This code will execute in the client computer, and it must put in the standard output the value of the attribute correspondent to this property.<br>The format of this value is 'name~description', where 'description' is optional.<br><b>Example of code:</b><br>#Create an attribute with the name of computer from bash<br> echo $HOSTNAME", null=True, verbose_name='code')),
                ('auto_add', models.BooleanField(default=True, help_text='automatically add the attribute to database', verbose_name='automatically add')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'Property',
                'verbose_name_plural': 'Properties',
            },
        ),
        migrations.CreateModel(
            name='Schedule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
            ],
            options={
                'verbose_name': 'Schedule',
                'verbose_name_plural': 'Schedules',
            },
        ),
        migrations.CreateModel(
            name='ScheduleDelay',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('delay', models.IntegerField(verbose_name='delay')),
                ('duration', models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)], verbose_name='duration')),
                ('attributes', models.ManyToManyField(blank=True, to='core.Attribute', verbose_name='attributes')),
                ('schedule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='delays', to='core.Schedule', verbose_name='schedule')),
            ],
            options={
                'verbose_name': 'Schedule Delay',
                'verbose_name_plural': 'Schedule Delays',
            },
        ),
        migrations.CreateModel(
            name='Store',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('slug', models.SlugField(unique=True, verbose_name='slug')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Project', verbose_name='project')),
            ],
            options={
                'ordering': ['name', 'project'],
                'verbose_name': 'Store',
                'verbose_name_plural': 'Stores',
            },
        ),
        migrations.AddField(
            model_name='package',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Project', verbose_name='project'),
        ),
        migrations.AddField(
            model_name='package',
            name='store',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Store', verbose_name='store'),
        ),
        migrations.AddField(
            model_name='deployment',
            name='available_packages',
            field=models.ManyToManyField(blank=True, help_text='If a computer has installed one of these packages it will be updated', to='core.Package', verbose_name='available packages'),
        ),
        migrations.AddField(
            model_name='deployment',
            name='excluded_attributes',
            field=models.ManyToManyField(blank=True, related_name='ExcludeAttribute', to='core.Attribute', verbose_name='excluded attributes'),
        ),
        migrations.AddField(
            model_name='deployment',
            name='included_attributes',
            field=models.ManyToManyField(blank=True, to='core.Attribute', verbose_name='included attributes'),
        ),
        migrations.AddField(
            model_name='deployment',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Project', verbose_name='project'),
        ),
        migrations.AddField(
            model_name='deployment',
            name='schedule',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Schedule', verbose_name='schedule'),
        ),
        migrations.AddField(
            model_name='attribute',
            name='property_att',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Property', verbose_name='Property'),
        ),
        migrations.CreateModel(
            name='BasicAttribute',
            fields=[
            ],
            options={
                'verbose_name': 'Basic Attribute',
                'proxy': True,
                'verbose_name_plural': 'Basic Attributes',
            },
            bases=('core.attribute',),
        ),
        migrations.CreateModel(
            name='BasicProperty',
            fields=[
            ],
            options={
                'verbose_name': 'Basic Property',
                'proxy': True,
                'verbose_name_plural': 'Basic Properties',
            },
            bases=('core.property',),
        ),
        migrations.CreateModel(
            name='ClientAttribute',
            fields=[
            ],
            options={
                'verbose_name': 'Feature',
                'proxy': True,
                'verbose_name_plural': 'Features',
            },
            bases=('core.attribute',),
        ),
        migrations.CreateModel(
            name='ClientProperty',
            fields=[
            ],
            options={
                'verbose_name': 'Formula',
                'proxy': True,
                'verbose_name_plural': 'Formulas',
            },
            bases=('core.property',),
        ),
        migrations.CreateModel(
            name='ServerAttribute',
            fields=[
            ],
            options={
                'verbose_name': 'Tag',
                'proxy': True,
                'verbose_name_plural': 'Tags',
            },
            bases=('core.attribute',),
        ),
        migrations.CreateModel(
            name='ServerProperty',
            fields=[
            ],
            options={
                'verbose_name': 'Stamp',
                'proxy': True,
                'verbose_name_plural': 'Stamps',
            },
            bases=('core.property',),
        ),
        migrations.AlterUniqueTogether(
            name='store',
            unique_together=set([('name', 'project')]),
        ),
        migrations.AlterUniqueTogether(
            name='scheduledelay',
            unique_together=set([('schedule', 'delay')]),
        ),
        migrations.AlterUniqueTogether(
            name='package',
            unique_together=set([('name', 'project')]),
        ),
        migrations.AlterUniqueTogether(
            name='deployment',
            unique_together=set([('name', 'project')]),
        ),
        migrations.AlterUniqueTogether(
            name='attribute',
            unique_together=set([('property_att', 'value')]),
        ),
    ]
