import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models

import migasfree.core.validators


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0004_alter_property'),
    ]

    operations = [
        migrations.AlterModelTableComment(
            name='attribute',
            table_comment='stores system attributes collected from computers via small scripts,',
        ),
        migrations.AlterModelTableComment(
            name='attributeset',
            table_comment='attribute sets',
        ),
        migrations.AlterModelTableComment(
            name='deployment',
            table_comment='repositories of packages and associated actions to be executed on computers',
        ),
        migrations.AlterModelTableComment(
            name='domain',
            table_comment='groups of computers managed by different administrators',
        ),
        migrations.AlterModelTableComment(
            name='package',
            table_comment='software package details: contains the name, version,',
        ),
        migrations.AlterModelTableComment(
            name='packageset',
            table_comment='sets of software packages associated with projects and stored in stores',
        ),
        migrations.AlterModelTableComment(
            name='platform',
            table_comment='collection of computer platforms (e.g. Linux, Windows, macOS)',
        ),
        migrations.AlterModelTableComment(
            name='project',
            table_comment='defines a customized set of computers with a specific distribution',
        ),
        migrations.AlterModelTableComment(
            name='property',
            table_comment='formulas used to gather attributes from computers',
        ),
        migrations.AlterModelTableComment(
            name='schedule',
            table_comment='enables the systematic planning of releases over time for specific attributes',
        ),
        migrations.AlterModelTableComment(
            name='scheduledelay',
            table_comment='stores delays for schedules, specifying when assigned attributes will be effective',
        ),
        migrations.AlterModelTableComment(
            name='scope',
            table_comment='customizable filter that allows users to define a specific set of computers',
        ),
        migrations.AlterModelTableComment(
            name='singularity',
            table_comment='exceptions to standard formulas used for gathering attributes from computers,',
        ),
        migrations.AlterModelTableComment(
            name='store',
            table_comment='locations for package storage',
        ),
        migrations.AlterModelTableComment(
            name='userprofile',
            table_comment='stores user-specific settings and preferences',
        ),
        migrations.AlterField(
            model_name='attribute',
            name='description',
            field=models.TextField(
                blank=True, db_comment='attribute description', null=True, verbose_name='description'
            ),
        ),
        migrations.AlterField(
            model_name='attribute',
            name='latitude',
            field=models.FloatField(
                blank=True, db_comment="latitude of the attribute set's geoposition", null=True, verbose_name='latitude'
            ),
        ),
        migrations.AlterField(
            model_name='attribute',
            name='longitude',
            field=models.FloatField(
                blank=True,
                db_comment="longitude of the attribute set's geoposition",
                null=True,
                verbose_name='longitude',
            ),
        ),
        migrations.AlterField(
            model_name='attribute',
            name='property_att',
            field=models.ForeignKey(
                db_comment='related property (formula)',
                on_delete=django.db.models.deletion.CASCADE,
                to='core.property',
                verbose_name='Property',
            ),
        ),
        migrations.AlterField(
            model_name='attribute',
            name='value',
            field=models.CharField(db_comment='attribute value', max_length=250, verbose_name='value'),
        ),
        migrations.AlterField(
            model_name='attributeset',
            name='description',
            field=models.TextField(
                blank=True, db_comment='attribute set description', null=True, verbose_name='description'
            ),
        ),
        migrations.AlterField(
            model_name='attributeset',
            name='enabled',
            field=models.BooleanField(
                db_comment='indicates whether the attribute set is enabled', default=True, verbose_name='enabled'
            ),
        ),
        migrations.AlterField(
            model_name='attributeset',
            name='latitude',
            field=models.FloatField(
                blank=True, db_comment="latitude of the attribute set's geoposition", null=True, verbose_name='latitude'
            ),
        ),
        migrations.AlterField(
            model_name='attributeset',
            name='longitude',
            field=models.FloatField(
                blank=True,
                db_comment="longitude of the attribute set's geoposition",
                null=True,
                verbose_name='longitude',
            ),
        ),
        migrations.AlterField(
            model_name='attributeset',
            name='name',
            field=models.CharField(db_comment='attribute set name', max_length=50, unique=True, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='deployment',
            name='base_url',
            field=models.CharField(
                blank=True, db_comment='external source base url', max_length=100, null=True, verbose_name='base url'
            ),
        ),
        migrations.AlterField(
            model_name='deployment',
            name='comment',
            field=models.TextField(blank=True, db_comment='deployment comments', null=True, verbose_name='comment'),
        ),
        migrations.AlterField(
            model_name='deployment',
            name='components',
            field=models.CharField(
                blank=True,
                db_comment='the various components of the source are listed (external)',
                max_length=100,
                null=True,
                verbose_name='components',
            ),
        ),
        migrations.AlterField(
            model_name='deployment',
            name='default_excluded_packages',
            field=models.TextField(
                blank=True,
                db_comment='packages to be uninstalled when tags are set on the computer',
                null=True,
                verbose_name='default excluded packages',
            ),
        ),
        migrations.AlterField(
            model_name='deployment',
            name='default_included_packages',
            field=models.TextField(
                blank=True,
                db_comment='packages to be installed when tags are set on the computer',
                null=True,
                verbose_name='default included packages',
            ),
        ),
        migrations.AlterField(
            model_name='deployment',
            name='default_preincluded_packages',
            field=models.TextField(
                blank=True,
                db_comment='can be used to install packages that configure repositories external to migasfree',
                null=True,
                verbose_name='default pre-included packages',
            ),
        ),
        migrations.AlterField(
            model_name='deployment',
            name='domain',
            field=models.ForeignKey(
                blank=True,
                db_comment='related domain',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='core.domain',
                verbose_name='domain',
            ),
        ),
        migrations.AlterField(
            model_name='deployment',
            name='enabled',
            field=models.BooleanField(
                db_comment='indicates whether deployment is enabled',
                default=True,
                help_text='if you uncheck this field, deployment is disabled for all computers.',
                verbose_name='enabled',
            ),
        ),
        migrations.AlterField(
            model_name='deployment',
            name='expire',
            field=models.IntegerField(
                db_comment="minutes that the public repository's metadata will remain cached (only taken into account "
                'in the case where the frozen is false)',
                default=1440,
                verbose_name='metadata cache minutes. Default 1440 minutes = 1 day',
            ),
        ),
        migrations.AlterField(
            model_name='deployment',
            name='frozen',
            field=models.BooleanField(
                db_comment='indicates whether the public repository metadata is updated or not',
                default=True,
                verbose_name='frozen',
            ),
        ),
        migrations.AlterField(
            model_name='deployment',
            name='name',
            field=models.CharField(db_comment='deployment name', max_length=50, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='deployment',
            name='options',
            field=models.CharField(
                blank=True,
                db_comment='allows you to specify the different options that we need for the external repository',
                max_length=250,
                null=True,
                verbose_name='options',
            ),
        ),
        migrations.AlterField(
            model_name='deployment',
            name='packages_to_install',
            field=models.TextField(
                blank=True,
                db_comment="lists the packages that will be automatically installed when a computer's attributes "
                'match the deployment',
                help_text='Mandatory packages to install each time',
                null=True,
                verbose_name='packages to install',
            ),
        ),
        migrations.AlterField(
            model_name='deployment',
            name='packages_to_remove',
            field=models.TextField(
                blank=True,
                db_comment="lists the packages that will be automatically removed when a computer's attributes "
                'match the deployment',
                help_text='Mandatory packages to remove each time',
                null=True,
                verbose_name='packages to remove',
            ),
        ),
        migrations.AlterField(
            model_name='deployment',
            name='project',
            field=models.ForeignKey(
                db_comment='related project',
                on_delete=django.db.models.deletion.CASCADE,
                to='core.project',
                verbose_name='project',
            ),
        ),
        migrations.AlterField(
            model_name='deployment',
            name='schedule',
            field=models.ForeignKey(
                blank=True,
                db_comment='related schedule',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='core.schedule',
                verbose_name='schedule',
            ),
        ),
        migrations.AlterField(
            model_name='deployment',
            name='slug',
            field=models.SlugField(db_comment='slug name', verbose_name='slug'),
        ),
        migrations.AlterField(
            model_name='deployment',
            name='source',
            field=models.CharField(
                choices=[('I', 'Internal'), ('E', 'External')],
                db_comment='indicates if the deployment originates from an internal (I) or external (E) source',
                default='I',
                max_length=1,
                verbose_name='source',
            ),
        ),
        migrations.AlterField(
            model_name='deployment',
            name='start_date',
            field=models.DateField(
                db_comment='initial date from which the deployment will be accessible',
                default=django.utils.timezone.now,
                verbose_name='start date',
            ),
        ),
        migrations.AlterField(
            model_name='deployment',
            name='suite',
            field=models.CharField(
                blank=True,
                db_comment='usually indicates the specific name of the distro (external source)',
                max_length=50,
                null=True,
                verbose_name='suite',
            ),
        ),
        migrations.AlterField(
            model_name='domain',
            name='comment',
            field=models.TextField(blank=True, db_comment='domain comments', null=True, verbose_name='comment'),
        ),
        migrations.AlterField(
            model_name='domain',
            name='name',
            field=models.CharField(db_comment='domain name', max_length=50, unique=True, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='package',
            name='architecture',
            field=models.CharField(db_comment='package architecture', max_length=10, verbose_name='architecture'),
        ),
        migrations.AlterField(
            model_name='package',
            name='fullname',
            field=models.CharField(
                db_comment='package fullname (name + version + architecture + extension)',
                max_length=170,
                verbose_name='fullname',
            ),
        ),
        migrations.AlterField(
            model_name='package',
            name='name',
            field=models.CharField(blank=True, db_comment='package name', max_length=100, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='package',
            name='project',
            field=models.ForeignKey(
                db_comment='related project',
                on_delete=django.db.models.deletion.CASCADE,
                to='core.project',
                verbose_name='project',
            ),
        ),
        migrations.AlterField(
            model_name='package',
            name='store',
            field=models.ForeignKey(
                db_comment='related store',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='core.store',
                verbose_name='store',
            ),
        ),
        migrations.AlterField(
            model_name='package',
            name='version',
            field=models.CharField(db_comment='package version', max_length=60, verbose_name='version'),
        ),
        migrations.AlterField(
            model_name='packageset',
            name='description',
            field=models.TextField(
                blank=True, db_comment='package set description', null=True, verbose_name='description'
            ),
        ),
        migrations.AlterField(
            model_name='packageset',
            name='name',
            field=models.CharField(db_comment='package set name', max_length=50, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='packageset',
            name='project',
            field=models.ForeignKey(
                db_comment='related project',
                on_delete=django.db.models.deletion.CASCADE,
                to='core.project',
                verbose_name='project',
            ),
        ),
        migrations.AlterField(
            model_name='packageset',
            name='store',
            field=models.ForeignKey(
                db_comment='related store',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='core.store',
                verbose_name='store',
            ),
        ),
        migrations.AlterField(
            model_name='platform',
            name='name',
            field=models.CharField(
                db_comment='platform name (Linux, Windows, ...)', max_length=50, unique=True, verbose_name='name'
            ),
        ),
        migrations.AlterField(
            model_name='project',
            name='architecture',
            field=models.CharField(
                db_comment='project architecture (amd64, i386, x86, x64, ...)',
                max_length=20,
                verbose_name='architecture',
            ),
        ),
        migrations.AlterField(
            model_name='project',
            name='auto_register_computers',
            field=models.BooleanField(
                db_comment='if true, it allows you to register the computer from a client automatically',
                default=False,
                help_text='Is not needed a user for register computers in database and get the keys.',
                verbose_name='auto register computers',
            ),
        ),
        migrations.AlterField(
            model_name='project',
            name='name',
            field=models.CharField(db_comment='project name', max_length=50, unique=True, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='project',
            name='platform',
            field=models.ForeignKey(
                db_comment='related platform',
                on_delete=django.db.models.deletion.CASCADE,
                to='core.platform',
                verbose_name='platform',
            ),
        ),
        migrations.AlterField(
            model_name='project',
            name='pms',
            field=models.CharField(
                choices=[
                    ('apt', 'apt'),
                    ('dnf', 'dnf'),
                    ('pacman', 'pacman'),
                    ('winget', 'winget'),
                    ('wpt', 'wpt'),
                    ('yum', 'yum'),
                    ('zypper', 'zypper'),
                ],
                db_comment="package management system utilized in the project's operating system",
                max_length=50,
                validators=[migasfree.core.validators.validate_project_pms],
                verbose_name='package management system',
            ),
        ),
        migrations.AlterField(
            model_name='project',
            name='slug',
            field=models.SlugField(db_comment='project name slug', unique=True, verbose_name='slug'),
        ),
        migrations.AlterField(
            model_name='property',
            name='auto_add',
            field=models.BooleanField(
                db_comment='automatically add the attribute to database',
                default=True,
                help_text='automatically add the attribute to database',
                verbose_name='automatically add',
            ),
        ),
        migrations.AlterField(
            model_name='property',
            name='code',
            field=models.TextField(
                blank=True,
                db_comment='instructions to execute on clients to obtain attributes',
                help_text='This code will execute in the client computer, and it must put in the standard output the '
                'value of the attribute correspondent to this property.<br>The format of this value is '
                "'name~description', where 'description' is optional.<br><b>Example of code:</b><br>#Create "
                'an attribute with the name of computer from bash<br> echo $HOSTNAME',
                null=True,
                verbose_name='code',
            ),
        ),
        migrations.AlterField(
            model_name='property',
            name='enabled',
            field=models.BooleanField(
                db_comment='indicates whether the property (formula) is enabled (if false, it will not be executed '
                'on the clients)',
                default=True,
                verbose_name='enabled',
            ),
        ),
        migrations.AlterField(
            model_name='property',
            name='kind',
            field=models.CharField(
                choices=[
                    ('N', 'Normal'),
                    ('-', 'List'),
                    ('L', 'Added to the left'),
                    ('R', 'Added to the right'),
                    ('J', 'JSON'),
                ],
                db_comment='property (formula) kind: normal, list, added to the left, added to the right',
                default='N',
                max_length=1,
                verbose_name='kind',
            ),
        ),
        migrations.AlterField(
            model_name='property',
            name='language',
            field=models.IntegerField(
                choices=[
                    (0, 'bash'),
                    (1, 'python'),
                    (2, 'perl'),
                    (3, 'php'),
                    (4, 'ruby'),
                    (5, 'cmd'),
                    (6, 'powershell'),
                ],
                db_comment='programming language in which the property (formula) code is written',
                default=0,
                verbose_name='programming language',
            ),
        ),
        migrations.AlterField(
            model_name='property',
            name='name',
            field=models.CharField(db_comment='property (formula) name', max_length=50, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='property',
            name='prefix',
            field=models.CharField(
                db_comment='it is a combination of three numbers or letters (used to group and identify attributes)',
                max_length=3,
                unique=True,
                verbose_name='prefix',
            ),
        ),
        migrations.AlterField(
            model_name='property',
            name='sort',
            field=models.CharField(
                choices=[('basic', 'Basic'), ('client', 'Client'), ('server', 'Server')],
                db_comment='property (formula) sort: basic (attribute), client (attribute), server (tag)',
                default='client',
                max_length=10,
                verbose_name='sort',
            ),
        ),
        migrations.AlterField(
            model_name='schedule',
            name='description',
            field=models.TextField(
                blank=True, db_comment='schedule description', null=True, verbose_name='description'
            ),
        ),
        migrations.AlterField(
            model_name='schedule',
            name='name',
            field=models.CharField(db_comment='schedule name', max_length=50, unique=True, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='scheduledelay',
            name='delay',
            field=models.IntegerField(
                db_comment='number of days from the deployment start date that the assigned attributes will be '
                'effective (Saturdays and Sundays are not taken into account)',
                verbose_name='delay',
            ),
        ),
        migrations.AlterField(
            model_name='scheduledelay',
            name='duration',
            field=models.IntegerField(
                db_comment='number of days to complete deployment to computers assigned to the delay',
                default=1,
                validators=[django.core.validators.MinValueValidator(1)],
                verbose_name='duration',
            ),
        ),
        migrations.AlterField(
            model_name='scheduledelay',
            name='schedule',
            field=models.ForeignKey(
                db_comment='related schedule',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='delays',
                to='core.schedule',
                verbose_name='schedule',
            ),
        ),
        migrations.AlterField(
            model_name='scope',
            name='domain',
            field=models.ForeignKey(
                blank=True,
                db_comment='related domain',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='core.domain',
                verbose_name='domain',
            ),
        ),
        migrations.AlterField(
            model_name='scope',
            name='name',
            field=models.CharField(db_comment='scope name', max_length=50, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='scope',
            name='user',
            field=models.ForeignKey(
                db_comment='related user profile',
                on_delete=django.db.models.deletion.CASCADE,
                to='core.userprofile',
                verbose_name='user',
            ),
        ),
        migrations.AlterField(
            model_name='singularity',
            name='code',
            field=models.TextField(
                blank=True,
                db_comment='instructions to execute on clients to obtain attributes',
                help_text='This code will execute in the client computer, and it must put in the standard output '
                'the value of the attribute correspondent to this property.<br>The format of this value is '
                "'name~description', where 'description' is optional.<br><b>Example of code:</b><br>"
                '#Create an attribute with the name of computer from bash<br> echo $HOSTNAME',
                null=True,
                verbose_name='code',
            ),
        ),
        migrations.AlterField(
            model_name='singularity',
            name='enabled',
            field=models.BooleanField(
                db_comment='indicates whether singularity is enabled', default=True, verbose_name='enabled'
            ),
        ),
        migrations.AlterField(
            model_name='singularity',
            name='language',
            field=models.IntegerField(
                choices=[
                    (0, 'bash'),
                    (1, 'python'),
                    (2, 'perl'),
                    (3, 'php'),
                    (4, 'ruby'),
                    (5, 'cmd'),
                    (6, 'powershell'),
                ],
                db_comment='programming language in which the singularity code is written',
                default=0,
                verbose_name='programming language',
            ),
        ),
        migrations.AlterField(
            model_name='singularity',
            name='name',
            field=models.CharField(
                db_comment='singularity name', default=None, max_length=50, unique=True, verbose_name='name'
            ),
        ),
        migrations.AlterField(
            model_name='singularity',
            name='priority',
            field=models.IntegerField(db_comment='singularity priority', verbose_name='priority'),
        ),
        migrations.AlterField(
            model_name='singularity',
            name='property_att',
            field=models.ForeignKey(
                db_comment='related property (formula)',
                on_delete=django.db.models.deletion.CASCADE,
                to='core.property',
                verbose_name='Property',
            ),
        ),
        migrations.AlterField(
            model_name='store',
            name='name',
            field=models.CharField(db_comment='store name', max_length=50, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='store',
            name='project',
            field=models.ForeignKey(
                db_comment='related project',
                on_delete=django.db.models.deletion.CASCADE,
                to='core.project',
                verbose_name='project',
            ),
        ),
        migrations.AlterField(
            model_name='store',
            name='slug',
            field=models.SlugField(db_comment='store slug name', verbose_name='slug'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='domain_preference',
            field=models.ForeignKey(
                blank=True,
                db_comment='domain that the user currently has selected in the application',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='core.domain',
                verbose_name='domain',
            ),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='scope_preference',
            field=models.ForeignKey(
                blank=True,
                db_comment='scope that the user currently has selected in the application',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='core.scope',
                verbose_name='scope',
            ),
        ),
    ]
