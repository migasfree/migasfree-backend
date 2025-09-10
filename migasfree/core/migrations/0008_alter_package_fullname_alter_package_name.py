from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0007_alter_project_pms'),
    ]

    operations = [
        migrations.AlterField(
            model_name='package',
            name='fullname',
            field=models.CharField(
                db_comment='package fullname (name + version + architecture + extension)',
                max_length=270,
                verbose_name='fullname',
            ),
        ),
        migrations.AlterField(
            model_name='package',
            name='name',
            field=models.CharField(
                blank=True,
                db_comment='package name',
                max_length=200,
                verbose_name='name',
            ),
        ),
    ]
