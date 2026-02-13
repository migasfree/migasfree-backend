import django.core.validators
from django.db import migrations, models

import migasfree.app_catalog.models


class Migration(migrations.Migration):
    dependencies = [
        ('app_catalog', '0003_add_gin_indexes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='icon',
            field=models.FileField(
                db_comment='application icon',
                null=True,
                storage=migasfree.app_catalog.models.MediaFileSystemStorage(),
                upload_to=migasfree.app_catalog.models.upload_path_handler,
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp', 'bmp', 'ico', 'tiff', 'tif']
                    )
                ],
                verbose_name='icon',
            ),
        ),
    ]
