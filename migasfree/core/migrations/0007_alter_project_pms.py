from django.db import migrations, models

import migasfree.core.validators


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0006_deployment_project'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='pms',
            field=models.CharField(
                choices=[
                    ('apt', 'apt'),
                    ('dnf', 'dnf'),
                    ('pacman', 'pacman'),
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
    ]
