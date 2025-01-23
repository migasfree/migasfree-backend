from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_alter_comments'),
    ]

    operations = [
        migrations.AddField(
            model_name='deployment',
            name='auto_restart',
            field=models.BooleanField(
                db_comment='indicates that start date is updated once the deployment is complete, ensuring an automatic restart of the process',
                default=False,
                verbose_name='auto restart'
            ),
        ),
        migrations.AddField(
            model_name='project',
            name='base_os',
            field=models.CharField(
                blank=True,
                db_comment='specifies the base operating system your project is based on',
                max_length=50,
                null=True,
                verbose_name='base operating system'
            ),
        ),
    ]
