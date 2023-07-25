from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_alter_singularity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='property',
            name='kind',
            field=models.CharField(
                choices=[('N', 'Normal'), ('-', 'List'), ('L', 'Added to the left'), ('R', 'Added to the right'), ('J', 'JSON')],
                default='N', max_length=1, verbose_name='kind'
            ),
        ),
    ]
