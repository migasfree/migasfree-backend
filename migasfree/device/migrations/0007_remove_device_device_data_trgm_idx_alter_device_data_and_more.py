import django.contrib.postgres.indexes
import django.db.models.functions.comparison
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_alter_project_pms'),
        ('device', '0006_device_device_name_trgm_idx_and_more'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='device',
            name='device_data_trgm_idx',
        ),
        migrations.RunSQL(
            sql='ALTER TABLE "device_device" ALTER COLUMN "data" TYPE jsonb USING (CASE WHEN "data" IS NULL OR "data" = \'\' THEN \'{}\'::jsonb ELSE "data"::jsonb END);',
            reverse_sql='ALTER TABLE "device_device" ALTER COLUMN "data" TYPE text;',
        ),
        migrations.AlterField(
            model_name='device',
            name='data',
            field=models.JSONField(blank=True, db_comment='list of fields and values for device connection', default=dict, null=True, verbose_name='data'),
        ),
        migrations.AddIndex(
            model_name='device',
            index=django.contrib.postgres.indexes.GinIndex(django.contrib.postgres.indexes.OpClass(django.db.models.functions.comparison.Cast('data', output_field=models.TextField()), name='gin_trgm_ops'), name='device_data_trgm_idx'),
        ),
    ]
