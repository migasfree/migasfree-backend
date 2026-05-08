from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0009_alter_deployment_start_date_alter_project_pms'),
    ]

    operations = [
        migrations.AlterModelTableComment(
            name='attribute',
            table_comment='stores system attributes collected from computers via small scripts, referred to as "formulas" (each attribute represents a specific characteristic of the computer, such as the number of hard drives, RAM size, or any other detail that can be retrieved through these automated formulas)',
        ),
        migrations.AlterModelTableComment(
            name='deployment',
            table_comment='repositories of packages and associated actions to be executed on computers that meet the required attributes',
        ),
        migrations.AlterModelTableComment(
            name='package',
            table_comment='software package details: contains the name, version, architecture, related project and store',
        ),
        migrations.AlterModelTableComment(
            name='scope',
            table_comment='customizable filter that allows users to define a specific set of computers based on attributes, simplifying tasks',
        ),
        migrations.AlterModelTableComment(
            name='singularity',
            table_comment='exceptions to standard formulas used for gathering attributes from computers, allowing different formulas to be specified based on unique computer attributes',
        ),
    ]
