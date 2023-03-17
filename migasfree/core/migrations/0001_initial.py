# Generated by Django 3.1.5 on 2021-01-19 08:56

import django.contrib.auth.models
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import migasfree.core.models.migas_link
import migasfree.core.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
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
                'verbose_name': 'Attribute',
                'verbose_name_plural': 'Attributes',
                'ordering': ['property_att__prefix', 'value'],
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.CreateModel(
            name='Domain',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='name')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='comment')),
                ('excluded_attributes', models.ManyToManyField(blank=True, related_name='domain_excluded', to='core.Attribute', verbose_name='excluded attributes')),
                ('included_attributes', models.ManyToManyField(blank=True, related_name='domain_included', to='core.Attribute', verbose_name='included attributes')),
            ],
            options={
                'verbose_name': 'Domain',
                'verbose_name_plural': 'Domains',
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.CreateModel(
            name='Package',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fullname', models.CharField(max_length=170, verbose_name='fullname')),
                ('name', models.CharField(blank=True, max_length=100, verbose_name='name')),
                ('version', models.CharField(max_length=60, verbose_name='version')),
                ('architecture', models.CharField(max_length=10, verbose_name='architecture')),
            ],
            options={
                'verbose_name': 'Package',
                'verbose_name_plural': 'Packages',
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.CreateModel(
            name='Platform',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='name')),
            ],
            options={
                'verbose_name': 'Platform',
                'verbose_name_plural': 'Platforms',
                'ordering': ['name'],
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='name')),
                ('slug', models.SlugField(unique=True, verbose_name='slug')),
                ('pms', models.CharField(choices=[('apt', 'apt'), ('dnf', 'dnf'), ('pacman', 'pacman'), ('winget', 'winget'), ('yum', 'yum'), ('zypper', 'zypper')], max_length=50, validators=[migasfree.core.validators.validate_project_pms], verbose_name='package management system')),
                ('architecture', models.CharField(max_length=20, verbose_name='architecture')),
                ('auto_register_computers', models.BooleanField(default=False, help_text='Is not needed a user for register computers in database and get the keys.', verbose_name='auto register computers')),
                ('platform', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.platform', verbose_name='platform')),
            ],
            options={
                'verbose_name': 'Project',
                'verbose_name_plural': 'Projects',
                'ordering': ['name'],
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.CreateModel(
            name='Property',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prefix', models.CharField(max_length=3, unique=True, verbose_name='prefix')),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('enabled', models.BooleanField(default=True, verbose_name='enabled')),
                ('kind', models.CharField(choices=[('N', 'Normal'), ('-', 'List'), ('L', 'Added to the left'), ('R', 'Added to the right')], default='N', max_length=1, verbose_name='kind')),
                ('sort', models.CharField(choices=[('basic', 'Basic'), ('client', 'Client'), ('server', 'Server')], default='client', max_length=10, verbose_name='sort')),
                ('auto_add', models.BooleanField(default=True, help_text='automatically add the attribute to database', verbose_name='automatically add')),
                ('language', models.IntegerField(choices=[(0, 'bash'), (1, 'python'), (2, 'perl'), (3, 'php'), (4, 'ruby'), (5, 'cmd'), (6, 'powershell')], default=0, verbose_name='programming language')),
                ('code', models.TextField(blank=True, help_text="This code will execute in the client computer, and it must put in the standard output the value of the attribute correspondent to this property.<br>The format of this value is 'name~description', where 'description' is optional.<br><b>Example of code:</b><br>#Create an attribute with the name of computer from bash<br> echo $HOSTNAME", null=True, verbose_name='code')),
            ],
            options={
                'verbose_name': 'Property',
                'verbose_name_plural': 'Properties',
                'ordering': ['name'],
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
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
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.CreateModel(
            name='Scope',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('domain', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.domain', verbose_name='domain')),
                ('excluded_attributes', models.ManyToManyField(blank=True, related_name='scope_excluded', to='core.Attribute', verbose_name='excluded attributes')),
                ('included_attributes', models.ManyToManyField(blank=True, related_name='scope_included', to='core.Attribute', verbose_name='included attributes')),
            ],
            options={
                'verbose_name': 'Scope',
                'verbose_name_plural': 'Scopes',
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('user_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='auth.user')),
                ('domain_preference', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.domain', verbose_name='domain')),
                ('domains', models.ManyToManyField(blank=True, related_name='domains', to='core.Domain', verbose_name='domains')),
                ('scope_preference', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.scope', verbose_name='scope')),
            ],
            options={
                'verbose_name': 'User Profile',
                'verbose_name_plural': 'User Profiles',
            },
            bases=('auth.user', migasfree.core.models.migas_link.MigasLink),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Store',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('slug', models.SlugField(verbose_name='slug')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.project', verbose_name='project')),
            ],
            options={
                'verbose_name': 'Store',
                'verbose_name_plural': 'Stores',
                'ordering': ['name', 'project'],
                'unique_together': {('name', 'project'), ('project', 'slug')},
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.AddField(
            model_name='scope',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.userprofile', verbose_name='user'),
        ),
        migrations.CreateModel(
            name='PackageSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('packages', models.ManyToManyField(blank=True, to='core.Package', verbose_name='packages')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.project', verbose_name='project')),
                ('store', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='core.store', verbose_name='store')),
            ],
            options={
                'verbose_name': 'Package Set',
                'verbose_name_plural': 'Package Sets',
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.AddField(
            model_name='package',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.project', verbose_name='project'),
        ),
        migrations.AddField(
            model_name='package',
            name='store',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='core.store', verbose_name='store'),
        ),
        migrations.CreateModel(
            name='Deployment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enabled', models.BooleanField(default=True, help_text='if you uncheck this field, deployment is disabled for all computers.', verbose_name='enabled')),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('slug', models.SlugField(verbose_name='slug')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='comment')),
                ('packages_to_install', models.TextField(blank=True, help_text='Mandatory packages to install each time', null=True, verbose_name='packages to install')),
                ('packages_to_remove', models.TextField(blank=True, help_text='Mandatory packages to remove each time', null=True, verbose_name='packages to remove')),
                ('start_date', models.DateField(default=django.utils.timezone.now, verbose_name='start date')),
                ('default_preincluded_packages', models.TextField(blank=True, null=True, verbose_name='default pre-included packages')),
                ('default_included_packages', models.TextField(blank=True, null=True, verbose_name='default included packages')),
                ('default_excluded_packages', models.TextField(blank=True, null=True, verbose_name='default excluded packages')),
                ('source', models.CharField(choices=[('I', 'Internal'), ('E', 'External')], default='I', max_length=1, verbose_name='source')),
                ('base_url', models.CharField(blank=True, max_length=100, null=True, verbose_name='base url')),
                ('options', models.CharField(blank=True, max_length=250, null=True, verbose_name='options')),
                ('suite', models.CharField(blank=True, max_length=50, null=True, verbose_name='suite')),
                ('components', models.CharField(blank=True, max_length=100, null=True, verbose_name='components')),
                ('frozen', models.BooleanField(default=True, verbose_name='frozen')),
                ('expire', models.IntegerField(default=1440, verbose_name='metadata cache minutes. Default 1440 minutes = 1 day')),
                ('available_package_sets', models.ManyToManyField(blank=True, help_text='If a computer has installed one of these packages it will be updated', to='core.PackageSet', verbose_name='available package sets')),
                ('available_packages', models.ManyToManyField(blank=True, help_text='If a computer has installed one of these packages it will be updated', to='core.Package', verbose_name='available packages')),
                ('domain', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.domain', verbose_name='domain')),
                ('excluded_attributes', models.ManyToManyField(blank=True, related_name='deployment_excluded', to='core.Attribute', verbose_name='excluded attributes')),
                ('included_attributes', models.ManyToManyField(blank=True, related_name='deployment_included', to='core.Attribute', verbose_name='included attributes')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.project', verbose_name='project')),
                ('schedule', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.schedule', verbose_name='schedule')),
            ],
            options={
                'verbose_name': 'Deployment',
                'verbose_name_plural': 'Deployments',
                'ordering': ['project__name', 'name'],
                'unique_together': {('name', 'project'), ('project', 'slug')},
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.CreateModel(
            name='AttributeSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('enabled', models.BooleanField(default=True, verbose_name='enabled')),
                ('longitude', models.FloatField(blank=True, null=True, verbose_name='longitude')),
                ('latitude', models.FloatField(blank=True, null=True, verbose_name='latitude')),
                ('excluded_attributes', models.ManyToManyField(blank=True, related_name='attributeset_excluded', to='core.Attribute', verbose_name='excluded attributes')),
                ('included_attributes', models.ManyToManyField(blank=True, related_name='attributeset_included', to='core.Attribute', verbose_name='included attributes')),
            ],
            options={
                'verbose_name': 'Attribute Set',
                'verbose_name_plural': 'Attribute Sets',
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.AddField(
            model_name='attribute',
            name='property_att',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.property', verbose_name='Property'),
        ),
        migrations.CreateModel(
            name='BasicAttribute',
            fields=[
            ],
            options={
                'verbose_name': 'Basic Attribute',
                'verbose_name_plural': 'Basic Attributes',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('core.attribute',),
        ),
        migrations.CreateModel(
            name='BasicProperty',
            fields=[
            ],
            options={
                'verbose_name': 'Basic Property',
                'verbose_name_plural': 'Basic Properties',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('core.property',),
        ),
        migrations.CreateModel(
            name='ClientAttribute',
            fields=[
            ],
            options={
                'verbose_name': 'Feature',
                'verbose_name_plural': 'Features',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('core.attribute',),
        ),
        migrations.CreateModel(
            name='ClientProperty',
            fields=[
            ],
            options={
                'verbose_name': 'Formula',
                'verbose_name_plural': 'Formulas',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('core.property',),
        ),
        migrations.CreateModel(
            name='ExternalSource',
            fields=[
            ],
            options={
                'verbose_name': 'Deployment (external source)',
                'verbose_name_plural': 'Deployments (external source)',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('core.deployment',),
        ),
        migrations.CreateModel(
            name='InternalSource',
            fields=[
            ],
            options={
                'verbose_name': 'Deployment (internal source)',
                'verbose_name_plural': 'Deployments (internal source)',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('core.deployment',),
        ),
        migrations.CreateModel(
            name='ServerAttribute',
            fields=[
            ],
            options={
                'verbose_name': 'Tag',
                'verbose_name_plural': 'Tags',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('core.attribute',),
        ),
        migrations.CreateModel(
            name='ServerProperty',
            fields=[
            ],
            options={
                'verbose_name': 'Stamp',
                'verbose_name_plural': 'Stamps',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('core.property',),
        ),
        migrations.AlterUniqueTogether(
            name='scope',
            unique_together={('name', 'domain', 'user')},
        ),
        migrations.CreateModel(
            name='ScheduleDelay',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('delay', models.IntegerField(verbose_name='delay')),
                ('duration', models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)], verbose_name='duration')),
                ('attributes', models.ManyToManyField(blank=True, to='core.Attribute', verbose_name='attributes')),
                ('schedule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='delays', to='core.schedule', verbose_name='schedule')),
            ],
            options={
                'verbose_name': 'Schedule Delay',
                'verbose_name_plural': 'Schedule Delays',
                'unique_together': {('schedule', 'delay')},
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
        migrations.AlterUniqueTogether(
            name='package',
            unique_together={('fullname', 'project')},
        ),
        migrations.AddField(
            model_name='domain',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='domain_tags', to='core.ServerAttribute', verbose_name='tags'),
        ),
        migrations.AlterUniqueTogether(
            name='attribute',
            unique_together={('property_att', 'value')},
        ),
    ]
