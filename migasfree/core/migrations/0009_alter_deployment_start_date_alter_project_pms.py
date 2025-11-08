import django.utils.timezone

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_alter_package_fullname_alter_package_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deployment',
            name='start_date',
            field=models.DateField(
                db_comment='initial date from which the deployment will be accessible',
                default=django.utils.timezone.localdate,
                verbose_name='start date'
            ),
        ),
    ]
