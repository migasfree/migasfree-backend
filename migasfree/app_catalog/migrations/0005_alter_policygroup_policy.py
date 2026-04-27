import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('app_catalog', '0004_alter_application_icon'),
    ]

    operations = [
        migrations.AlterField(
            model_name='policygroup',
            name='policy',
            field=models.ForeignKey(
                db_comment='related policy',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='groups',
                to='app_catalog.policy',
                verbose_name='policy',
            ),
        ),
    ]
