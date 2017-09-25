# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-14 12:38
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import markdownx.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='name')),
                ('description', markdownx.models.MarkdownxField(blank=True, help_text='markdown syntax allowed', verbose_name='description')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='date')),
                ('score', models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], default=1, help_text='Relevance to the organization', verbose_name='score')),
                ('icon', models.ImageField(null=True, upload_to=b'catalog_icons/', verbose_name='icon')),
                ('level', models.CharField(choices=[(b'U', 'User'), (b'A', 'Admin')], default=b'U', max_length=1, verbose_name='level')),
                ('category', models.IntegerField(choices=[(1, 'Accessories'), (2, 'Books'), (3, 'Developers Tools'), (4, 'Education'), (5, 'Fonts'), (6, 'Games'), (7, 'Graphics'), (8, 'Internet'), (9, 'Medicine'), (10, 'Office'), (11, 'Science & Engineering'), (12, 'Sound & Video'), (13, 'Themes & Tweaks'), (14, 'Universal Access')], default=1, verbose_name='category')),
            ],
            options={
                'verbose_name': 'Application',
                'verbose_name_plural': 'Applications',
            },
        ),
        migrations.CreateModel(
            name='PackagesByProject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('packages_to_install', models.TextField(blank=True, verbose_name='packages to install')),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='packages_by_project', to='app_catalog.Application', verbose_name='application')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Project', verbose_name='project')),
            ],
            options={
                'verbose_name': 'Packages by Project',
                'verbose_name_plural': 'Packages by Projects',
            },
        ),
        migrations.CreateModel(
            name='Policy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('enabled', models.BooleanField(default=True, help_text='if you uncheck this field, the policy is disabled for all computers.', verbose_name='enabled')),
                ('exclusive', models.BooleanField(default=True, verbose_name='exclusive')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='comment')),
                ('excluded_attributes', models.ManyToManyField(blank=True, related_name='PolicyExcludedAttributes', to='core.Attribute', verbose_name='excluded attributes')),
                ('included_attributes', models.ManyToManyField(blank=True, related_name='PolicyIncludedAttributes', to='core.Attribute', verbose_name='included attributes')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'Policy',
                'verbose_name_plural': 'Policies',
            },
        ),
        migrations.CreateModel(
            name='PolicyGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('priority', models.IntegerField(verbose_name='priority')),
                ('applications', models.ManyToManyField(blank=True, to='app_catalog.Application', verbose_name='application')),
                ('excluded_attributes', models.ManyToManyField(blank=True, related_name='PolicyGroupExcludedAttributes', to='core.Attribute', verbose_name='excluded attributes')),
                ('included_attributes', models.ManyToManyField(blank=True, related_name='PolicyGroupIncludedAttributes', to='core.Attribute', verbose_name='included attributes')),
                ('policy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app_catalog.Policy', verbose_name='policy')),
            ],
            options={
                'ordering': ['policy__name', 'priority'],
                'verbose_name': 'Policy Group',
                'verbose_name_plural': 'Policy Groups',
            },
        ),
        migrations.AlterUniqueTogether(
            name='policygroup',
            unique_together=set([('policy', 'priority')]),
        ),
        migrations.AlterUniqueTogether(
            name='policy',
            unique_together=set([('name',)]),
        ),
        migrations.AlterUniqueTogether(
            name='packagesbyproject',
            unique_together=set([('application', 'project')]),
        ),
    ]