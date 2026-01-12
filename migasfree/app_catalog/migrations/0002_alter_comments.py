import django.db.models.deletion
import markdownx.models
from django.db import migrations, models

import migasfree.app_catalog.models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0005_alter_comments'),
        ('app_catalog', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelTableComment(
            name='application',
            table_comment='application catalog of the organization',
        ),
        migrations.AlterModelTableComment(
            name='category',
            table_comment='application categories',
        ),
        migrations.AlterModelTableComment(
            name='packagesbyproject',
            table_comment='packages to install applications per project',
        ),
        migrations.AlterModelTableComment(
            name='policy',
            table_comment='they allow complex orders to be given for installing and uninstalling applications',
        ),
        migrations.AlterModelTableComment(
            name='policygroup',
            table_comment='app installation policy priority list',
        ),
        migrations.AlterField(
            model_name='application',
            name='category',
            field=models.ForeignKey(
                db_comment='application category (used to classify the application)',
                on_delete=django.db.models.deletion.CASCADE,
                to='app_catalog.category',
                verbose_name='category',
            ),
        ),
        migrations.AlterField(
            model_name='application',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True,
                db_comment='date of entry of the application into the migasfree system',
                verbose_name='date',
            ),
        ),
        migrations.AlterField(
            model_name='application',
            name='description',
            field=markdownx.models.MarkdownxField(
                blank=True,
                db_comment='application description',
                help_text='markdown syntax allowed',
                verbose_name='description',
            ),
        ),
        migrations.AlterField(
            model_name='application',
            name='icon',
            field=models.ImageField(
                db_comment='application icon',
                null=True,
                storage=migasfree.app_catalog.models.MediaFileSystemStorage(),
                upload_to=migasfree.app_catalog.models.upload_path_handler,
                verbose_name='icon',
            ),
        ),
        migrations.AlterField(
            model_name='application',
            name='level',
            field=models.CharField(
                choices=[('U', 'User'), ('A', 'Admin')],
                db_comment=(
                    'single-character string: Use "U" for User level (no privileges required) and "A" for '
                    'Administrator level (requires elevated privileges)'
                ),
                default='U',
                max_length=1,
                verbose_name='level',
            ),
        ),
        migrations.AlterField(
            model_name='application',
            name='name',
            field=models.CharField(db_comment='application name', max_length=50, unique=True, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='application',
            name='score',
            field=models.IntegerField(
                choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)],
                db_comment='relevance of the application to the organization (1 = lowest, 5 = highest)',
                default=1,
                help_text='Relevance to the organization',
                verbose_name='score',
            ),
        ),
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(
                db_comment='application category name', max_length=50, unique=True, verbose_name='name'
            ),
        ),
        migrations.AlterField(
            model_name='packagesbyproject',
            name='application',
            field=models.ForeignKey(
                db_comment='related application',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='packages_by_project',
                to='app_catalog.application',
                verbose_name='application',
            ),
        ),
        migrations.AlterField(
            model_name='packagesbyproject',
            name='packages_to_install',
            field=models.TextField(
                blank=True,
                db_comment='list of packages for the application to be installed',
                verbose_name='packages to install',
            ),
        ),
        migrations.AlterField(
            model_name='packagesbyproject',
            name='project',
            field=models.ForeignKey(
                db_comment='project in which the application will be available',
                on_delete=django.db.models.deletion.CASCADE,
                to='core.project',
                verbose_name='project',
            ),
        ),
        migrations.AlterField(
            model_name='policy',
            name='comment',
            field=models.TextField(blank=True, db_comment='policy description', null=True, verbose_name='comment'),
        ),
        migrations.AlterField(
            model_name='policy',
            name='enabled',
            field=models.BooleanField(
                db_comment='indicates whether or not the policy is enabled',
                default=True,
                help_text='if you uncheck this field, the policy is disabled for all computers.',
                verbose_name='enabled',
            ),
        ),
        migrations.AlterField(
            model_name='policy',
            name='exclusive',
            field=models.BooleanField(
                db_comment=(
                    'it is ordered to uninstall the applications assigned in the priorities that have not been met'
                ),
                default=True,
                verbose_name='exclusive',
            ),
        ),
        migrations.AlterField(
            model_name='policy',
            name='name',
            field=models.CharField(db_comment='policy name', max_length=50, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='policygroup',
            name='policy',
            field=models.ForeignKey(
                db_comment='related policy',
                on_delete=django.db.models.deletion.CASCADE,
                to='app_catalog.policy',
                verbose_name='policy',
            ),
        ),
        migrations.AlterField(
            model_name='policygroup',
            name='priority',
            field=models.IntegerField(
                db_comment='integer used to indicate the order in which different policy groups will be processed',
                verbose_name='priority',
            ),
        ),
    ]
