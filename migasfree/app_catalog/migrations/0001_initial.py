from django.db import migrations, models
import django.db.models.deletion
import markdownx.models
import migasfree.app_catalog.models
import migasfree.core.models.migas_link


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='name')),
            ],
            options={
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
            },
        ),
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='name')),
                ('description', markdownx.models.MarkdownxField(blank=True, help_text='markdown syntax allowed', verbose_name='description')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='date')),
                ('score', models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], default=1, help_text='Relevance to the organization', verbose_name='score')),
                ('icon', models.ImageField(null=True, storage=migasfree.app_catalog.models.MediaFileSystemStorage(), upload_to=migasfree.app_catalog.models.upload_path_handler, verbose_name='icon')),
                ('level', models.CharField(choices=[('U', 'User'), ('A', 'Admin')], default='U', max_length=1, verbose_name='level')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app_catalog.category', verbose_name='category')),
                ('available_for_attributes', models.ManyToManyField(blank=True, to='core.Attribute', verbose_name='available for attributes')),
            ],
            options={
                'verbose_name': 'Application',
                'verbose_name_plural': 'Applications',
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.CreateModel(
            name='Policy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('enabled', models.BooleanField(default=True, help_text='if you uncheck this field, the policy is disabled for all computers.', verbose_name='enabled')),
                ('exclusive', models.BooleanField(default=True, verbose_name='exclusive')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='comment')),
                ('excluded_attributes', models.ManyToManyField(blank=True, related_name='policy_excluded', to='core.Attribute', verbose_name='excluded attributes')),
                ('included_attributes', models.ManyToManyField(blank=True, related_name='policy_included', to='core.Attribute', verbose_name='included attributes')),
            ],
            options={
                'verbose_name': 'Policy',
                'verbose_name_plural': 'Policies',
                'ordering': ['name'],
                'unique_together': {('name',)},
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.CreateModel(
            name='PolicyGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('priority', models.IntegerField(verbose_name='priority')),
                ('applications', models.ManyToManyField(blank=True, to='app_catalog.Application', verbose_name='application')),
                ('excluded_attributes', models.ManyToManyField(blank=True, related_name='policygroup_excluded', to='core.Attribute', verbose_name='excluded attributes')),
                ('included_attributes', models.ManyToManyField(blank=True, related_name='policygroup_included', to='core.Attribute', verbose_name='included attributes')),
                ('policy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app_catalog.policy', verbose_name='policy')),
            ],
            options={
                'verbose_name': 'Policy Group',
                'verbose_name_plural': 'Policy Groups',
                'ordering': ['policy__name', 'priority'],
                'unique_together': {('policy', 'priority')},
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.CreateModel(
            name='PackagesByProject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('packages_to_install', models.TextField(blank=True, verbose_name='packages to install')),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='packages_by_project', to='app_catalog.application', verbose_name='application')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.project', verbose_name='project')),
            ],
            options={
                'verbose_name': 'Packages by Project',
                'verbose_name_plural': 'Packages by Projects',
                'ordering': ['application__id', 'project__name'],
                'unique_together': {('application', 'project')},
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
    ]
