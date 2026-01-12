import django.db.models.deletion
from django.db import migrations, models

import migasfree.core.models.migas_link
import migasfree.core.validators


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='pms',
            field=models.CharField(
                choices=[
                    ('apt', 'apt'),
                    ('dnf', 'dnf'),
                    ('giman', 'plugins.giman'),
                    ('gpkgmgr', 'plugins.gpkgmgr'),
                    ('pacman', 'pacman'),
                    ('winget', 'winget'),
                    ('yum', 'yum'),
                    ('zypper', 'zypper'),
                ],
                max_length=50,
                validators=[migasfree.core.validators.validate_project_pms],
                verbose_name='package management system',
            ),
        ),
        migrations.CreateModel(
            name='Singularity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enabled', models.BooleanField(default=True, verbose_name='enabled')),
                ('priority', models.IntegerField(verbose_name='priority')),
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
                (
                    'code',
                    models.TextField(
                        blank=True,
                        help_text='This code will execute in the client computer, and it must put in the standard '
                        'output the value of the attribute correspondent to this property.<br>The format of this value '
                        "is 'name~description', where 'description' is optional.<br><b>Example of code:</b>"
                        '<br>#Create an attribute with the name of computer from bash<br> echo $HOSTNAME',
                        null=True,
                        verbose_name='code',
                    ),
                ),
                (
                    'excluded_attributes',
                    models.ManyToManyField(
                        blank=True,
                        related_name='singularity_excluded',
                        to='core.Attribute',
                        verbose_name='excluded attributes',
                    ),
                ),
                (
                    'included_attributes',
                    models.ManyToManyField(
                        blank=True,
                        related_name='singularity_included',
                        to='core.Attribute',
                        verbose_name='included attributes',
                    ),
                ),
                (
                    'property_att',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='core.property', verbose_name='Property'
                    ),
                ),
            ],
            options={
                'verbose_name': 'Singularity',
                'verbose_name_plural': 'Singularities',
                'ordering': ['property_att__name', 'priority'],
            },
            bases=(models.Model, migasfree.core.models.migas_link.MigasLink),
        ),
    ]
