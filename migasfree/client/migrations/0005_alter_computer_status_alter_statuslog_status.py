from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('client', '0004_add_gin_indexes'),
    ]

    operations = [
        migrations.RunSQL(
            sql="UPDATE client_computer SET status = 'assigned' WHERE status = 'intended';",
            reverse_sql="UPDATE client_computer SET status = 'intended' WHERE status = 'assigned';",
        ),
        migrations.RunSQL(
            sql="UPDATE client_statuslog SET status = 'assigned' WHERE status = 'intended';",
            reverse_sql="UPDATE client_statuslog SET status = 'intended' WHERE status = 'assigned';",
        ),
        migrations.AlterField(
            model_name='computer',
            name='status',
            field=models.CharField(
                choices=[
                    ('assigned', 'Assigned'),
                    ('reserved', 'Reserved'),
                    ('unknown', 'Unknown'),
                    ('in repair', 'In repair'),
                    ('available', 'Available'),
                    ('unsubscribed', 'Unsubscribed'),
                ],
                db_comment='computer status: assigned, reserved, unknown, in repair, available or unsubscribed',
                default='assigned',
                max_length=20,
                verbose_name='status',
            ),
        ),
        migrations.AlterField(
            model_name='statuslog',
            name='status',
            field=models.CharField(
                choices=[
                    ('assigned', 'Assigned'),
                    ('reserved', 'Reserved'),
                    ('unknown', 'Unknown'),
                    ('in repair', 'In repair'),
                    ('available', 'Available'),
                    ('unsubscribed', 'Unsubscribed'),
                ],
                db_comment='computer status on a specific date',
                default='assigned',
                max_length=20,
                verbose_name='status',
            ),
        ),
    ]
