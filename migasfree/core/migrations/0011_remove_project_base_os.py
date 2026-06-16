from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0010_alter_attribute_table_comment_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='base_os',
        ),
    ]
