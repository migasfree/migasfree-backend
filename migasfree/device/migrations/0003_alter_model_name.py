from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('device', '0002_alter_comments'),
    ]

    operations = [
        migrations.AlterField(
            model_name='model',
            name='name',
            field=models.CharField(
                blank=True,
                db_comment='device model name',
                db_index=True,
                max_length=50,
                null=True,
                verbose_name='name',
            ),
        ),
    ]
