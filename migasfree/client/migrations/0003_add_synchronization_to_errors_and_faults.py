import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('client', '0002_alter_comments'),
    ]

    operations = [
        migrations.AddField(
            model_name='error',
            name='synchronization',
            field=models.ForeignKey(
                blank=True,
                db_comment='synchronization that generated this error',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='errors',
                to='client.synchronization',
                verbose_name='synchronization',
            ),
        ),
        migrations.AddField(
            model_name='fault',
            name='synchronization',
            field=models.ForeignKey(
                blank=True,
                db_comment='synchronization that generated this fault',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='faults',
                to='client.synchronization',
                verbose_name='synchronization',
            ),
        ),
    ]
