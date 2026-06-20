import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('mgi', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='flavour',
            name='config',
            field=models.ForeignKey(
                db_comment='related MGI configuration',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='flavours',
                to='mgi.config',
                verbose_name='MGI Config',
            ),
        ),
        migrations.AlterField(
            model_name='release',
            name='config',
            field=models.ForeignKey(
                db_comment='related MGI configuration',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='releases',
                to='mgi.config',
                verbose_name='MGI Config',
            ),
        ),
    ]
